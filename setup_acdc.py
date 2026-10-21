"""
setup_acdc.py
=============
Prepares a Cell-ACDC folder structure from raw .nd2 files.

Given a source folder laid out as:
    <src>/
        somefile.nd2
        anotherfile.nd2
        dw/
            somefile_dw.tif
            somefile_dw_max.tif    ← skipped
            anotherfile_dw.tif
            masks/
                somefile_dw_mask.tif
                anotherfile_dw_mask.tif

This script creates:
    <src>/acdc/
        Position_1/Images/
            somefile_s1_DAPI.tif         ← channel 0 from .nd2
            somefile_s1_GFP.tif          ← channel 1 from .nd2
            somefile_s1_DAPI_dw.tif      ← channel 0 from dw/_dw.tif
            somefile_s1_GFP_dw.tif       ← channel 1 from dw/_dw.tif
            somefile_dw_segm.npz         ← converted from dw/masks/
        Position_2/Images/
            ...

Usage:
    python setup_acdc.py /path/to/folder \\
        --rawChannels DAPI GFP mCherry \\
        --deconvolvedChannels DAPI GFP mCherry
"""

import sys
import argparse
import numpy as np
import tifffile
from pathlib import Path


# ------------------------------------------------------------------ #
# Readers
# ------------------------------------------------------------------ #

def read_nd2_channels(nd2_path: Path) -> np.ndarray:
    """
    Read an .nd2 file and return a (C, spatial...) array using bioio.
    Prints full diagnostics so failures are never silent.
    """
    import traceback
    from bioio import BioImage

    try:
        img = BioImage(nd2_path)

        T, C, Z, Y, X = img.shape
        print(f"    shape (TCZYX): T={T} C={C} Z={Z} Y={Y} X={X}  dtype={img.dtype}")

        spatial_axes = ("Z" if Z > 1 else "") + "YX"
        dim_str      = "C" + spatial_axes        # "CZYX" or "CYX"
        kwargs       = {"T": 0} if T > 1 else {}

        data = img.get_image_data(dim_str, **kwargs)
        print(f"    get_image_data('{dim_str}') → shape {data.shape}")

        # Guard: if C axis was squeezed away, restore it
        if data.ndim == len(spatial_axes):
            data = data[np.newaxis]
            print(f"    C axis was missing, added → shape {data.shape}")

        return data   # (C, [Z,] Y, X)

    except Exception as e:
        print(f"    ERROR reading {nd2_path.name}:")
        traceback.print_exc()
        raise


def read_tif_channels(tif_path: Path) -> np.ndarray:
    """
    Read a multi-channel .tif and return a (C, spatial...) array.

    tifffile gives us a raw ndarray with no guaranteed axis labelling.
    We use the tifffile metadata (axes tag) when available, and fall back
    to a shape-based heuristic otherwise.
    """
    with tifffile.TiffFile(tif_path) as tf:
        data  = tf.asarray()
        # tifffile sometimes records the axes string in the metadata
        axes  = getattr(tf.series[0], "axes", "") if tf.series else ""

    print(f"    tif raw shape {data.shape}  axes tag='{axes}'  dtype {data.dtype}")

    # Normalise axes tag to upper-case and strip T if singleton
    axes = axes.upper()

    if axes:
        # Use the metadata axes string to find C
        if "C" in axes:
            c_idx = axes.index("C")
            # Move C to axis 0
            data = np.moveaxis(data, c_idx, 0)
            return data
        else:
            # No channel axis recorded → treat as single channel
            return data[np.newaxis]

    # --- fallback: shape heuristic ---
    if data.ndim == 2:      # YX
        return data[np.newaxis]
    if data.ndim == 3:      # most likely CYX or ZYX
        # If first dim is small (≤ 8) treat as C, else treat as Z → 1 channel
        if data.shape[0] <= 8:
            return data     # (C, Y, X)
        else:
            return data[np.newaxis]   # (1, Z, Y, X) — single channel stack
    if data.ndim == 4:      # CZYX
        return data
    raise ValueError(f"Unexpected shape {data.shape} in {tif_path}")


# ------------------------------------------------------------------ #
# Metadata extraction
# ------------------------------------------------------------------ #

def extract_metadata(nd2_path: Path, out_path: Path, position: int, channel_names: list):
    """
    Extract key metadata from an .nd2 file and write to a text file.
    Uses bioio for consistency with the rest of the script.
    """
    from bioio import BioImage
    img = BioImage(nd2_path)

    lines = [
        f"File:             {nd2_path.name}",
        f"Position:         {position}",
        f"Dimensions:       {dict(img.dims)}",
        f"Shape (TCZYX):    {img.shape}",
        f"Physical pixel sizes (ZYX um): "
        f"Z={img.physical_pixel_sizes.Z}, "
        f"Y={img.physical_pixel_sizes.Y}, "
        f"X={img.physical_pixel_sizes.X}",
        f"Channel names (raw): {channel_names}",
        f"dtype:            {img.dtype}",
    ]

    # Try to get richer metadata if available
    try:
        meta = img.metadata
        lines.append(f"\nFull metadata:\n{meta}")
    except Exception:
        pass

    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")


# ------------------------------------------------------------------ #
# Mask conversion
# ------------------------------------------------------------------ #

def convert_mask(mask_path: Path, out_path: Path) -> tuple:
    mask = tifffile.imread(mask_path)
    np.savez(out_path, mask)
    return mask.shape


# ------------------------------------------------------------------ #
# Main
# ------------------------------------------------------------------ #

def main():
    parser = argparse.ArgumentParser(
        description="Set up Cell-ACDC folder structure from .nd2 files."
    )
    parser.add_argument("folder", help="Source folder containing .nd2 files")
    parser.add_argument(
        "--rawChannels", nargs="+", required=True,
        metavar="NAME",
        help="Channel names for the raw .nd2 files, in order (e.g. DAPI GFP mCherry)"
    )
    parser.add_argument(
        "--deconvolvedChannels", nargs="+", required=True,
        metavar="NAME",
        help="Channel names for the _dw.tif files, in order"
    )
    args = parser.parse_args()

    src           = Path(args.folder).resolve()
    raw_channels  = args.rawChannels
    dw_channels   = args.deconvolvedChannels
    dw_dir        = src / "dw"
    mask_dir      = dw_dir / "masks"
    acdc_dir      = src / "acdc"

    if not src.is_dir():
        print(f"Error: not a directory: {src}")
        sys.exit(1)

    nd2_files = sorted(src.glob("*.nd2"))
    if not nd2_files:
        print("No .nd2 files found in", src)
        sys.exit(1)

    print(f"Found {len(nd2_files)} .nd2 file(s)")
    print(f"Raw channels:         {raw_channels}")
    print(f"Deconvolved channels: {dw_channels}\n")

    acdc_dir.mkdir(exist_ok=True)
    warnings = []

    for i, nd2_path in enumerate(nd2_files, start=1):
        stem        = nd2_path.stem          # e.g. "somefile"
        pos_images  = acdc_dir / f"Position_{i}" / "Images"
        pos_images.mkdir(parents=True, exist_ok=True)

        print(f"Position_{i}  ←  {nd2_path.name}")

        # ---- 1. Split .nd2 by channel → individual .tif files ----------
        print(f"  Reading {nd2_path.name} ...")
        try:
            raw_data = read_nd2_channels(nd2_path)   # (C, Z, Y, X)
            n_raw = raw_data.shape[0]

            if n_raw != len(raw_channels):
                msg = (f"  [WARN] .nd2 has {n_raw} channel(s) but "
                       f"{len(raw_channels)} rawChannels given — "
                       f"using min({n_raw}, {len(raw_channels)})")
                print(msg); warnings.append(msg)

            for c, ch_name in enumerate(raw_channels[:n_raw]):
                out_name = f"{stem}_{ch_name}.tif"
                tifffile.imwrite(pos_images / out_name, raw_data[c])
                print(f"  [raw]    channel {c} → {out_name}  shape={raw_data[c].shape}")

        except Exception as e:
            msg = f"  [ERROR] Could not read {nd2_path.name}: {e}"
            print(msg); warnings.append(msg)

        # ---- 1b. Extract metadata ---------------------------------------
        try:
            meta_path = pos_images / "metadata.txt"
            extract_metadata(nd2_path, meta_path, i, raw_channels)
            print(f"  [meta]   metadata.txt written")
        except Exception as e:
            msg = f"  [WARN] Could not extract metadata: {e}"
            print(msg); warnings.append(msg)

        # ---- 2. Split _dw.tif by channel --------------------------------
        dw_file = dw_dir / f"{stem}_dw.tif"
        if dw_file.exists():
            try:
                dw_data = read_tif_channels(dw_file)   # (C, ...)
                n_dw = dw_data.shape[0]

                if n_dw != len(dw_channels):
                    msg = (f"  [WARN] _dw.tif has {n_dw} channel(s) but "
                           f"{len(dw_channels)} deconvolvedChannels given — "
                           f"using min({n_dw}, {len(dw_channels)})")
                    print(msg); warnings.append(msg)

                for c, ch_name in enumerate(dw_channels[:n_dw]):
                    out_name = f"{stem}_{ch_name}_dw.tif"
                    tifffile.imwrite(pos_images / out_name, dw_data[c])
                    print(f"  [dw]     channel {c} → {out_name}  shape={dw_data[c].shape}")

            except Exception as e:
                msg = f"  [ERROR] Could not read {dw_file.name}: {e}"
                print(msg); warnings.append(msg)
        else:
            msg = f"  [MISSING] {dw_file.name}  (expected in dw/)"
            print(msg); warnings.append(msg)

        # ---- 3. Convert masks → .npz ------------------------------------
        # Look for per-channel subdirs: masks_<channelName>/
        channel_mask_dirs = sorted(
            d for d in mask_dir.iterdir()
            if d.is_dir() and d.name.startswith("masks_")
        ) if mask_dir.exists() else []

        if channel_mask_dirs:
            # Per-channel subfolder mode: masks_DAPI/, masks_GFP/, …
            for ch_dir in channel_mask_dirs:
                ch_name = ch_dir.name[len("masks_"):]   # strip "masks_" prefix
                # Find the tif for this stem in the channel subfolder
                mask_file = ch_dir / f"{stem}_dw_mask.tif"
                if not mask_file.exists():
                    # Try any tif whose stem starts with our image stem
                    candidates = list(ch_dir.glob(f"{stem}*.tif"))
                    mask_file = candidates[0] if candidates else None

                if mask_file and mask_file.exists():
                    npz_name = f"{stem}_{ch_name}_segm.npz"
                    shape = convert_mask(mask_file, pos_images / npz_name)
                    print(f"  [mask]   {ch_dir.name}/{mask_file.name} → {npz_name}  shape={shape}")
                else:
                    msg = f"  [MISSING] mask for {stem} in {ch_dir.name}/"
                    print(msg); warnings.append(msg)

        else:
            # Flat mode: single mask file per image in masks/
            mask_file = mask_dir / f"{stem}_dw_mask.tif" if mask_dir.exists() else None
            if mask_file and mask_file.exists():
                npz_name = f"{stem}_dw_segm.npz"
                shape = convert_mask(mask_file, pos_images / npz_name)
                print(f"  [mask]   {mask_file.name} → {npz_name}  shape={shape}")
            else:
                msg = f"  [MISSING] {stem}_dw_mask.tif  (expected in dw/masks/)"
                print(msg); warnings.append(msg)

        print()

    # ------------------------------------------------------------------ #
    # Summary
    # ------------------------------------------------------------------ #
    print(f"Done — {len(nd2_files)} position(s) written to:\n  {acdc_dir}")
    if warnings:
        print(f"\n{len(warnings)} warning(s):")
        for w in warnings:
            print(" ", w.strip())


if __name__ == "__main__":
    main()
