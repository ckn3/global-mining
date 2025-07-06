# Data Processing Scripts Documentation

This directory contains scripts for processing raw data to generate training datasets for SAM2 mining area segmentation.

## File Descriptions

### 1. `count_images.py` - Generate Base Site Counts
- **Function**: Analyze metadata and generate base site counts with split assignments
- **Input**: 
  - `metadata/image_file_metadata.csv` - Image metadata
- **Output**: 
  - `misc/base_site_counts.csv` - Base site counts with train/val/test splits
- **Note**: This script is used to generate the base site counts and split mapping. It is not used to split the dataset into train/val/test. The split is done by manually adding the split column to the base_site_counts.csv file.

### 2. `create_gt.py` - Generate Ground Truth Labels
- **Function**: Generate 3-class labels (background=0, cloud=1, mining=2) from KML files and original TIFF images
- **Input**: 
  - `metadata/global_mining_extents_detailed.kml` - Mining area boundaries
  - `metadata/image_file_metadata.csv` - Image metadata
  - `mining_ndvi_timeseries/` - Original 8-band TIFF images
- **Output**: 
  - `data/images/` - 7-band TIFF images (bands 1-7)
  - `data/labels/` - PNG label images with values 0, 1, 2

### 3. `generate_rgb.py` - Generate RGB Visualizations
- **Function**: Create RGB visualizations from 7-band TIFF images
- **Input**: `data/images/` - 7-band TIFF images
- **Output**: `data/rgb/` - RGB PNG images (bands 3-2-1)

### 4. `reorganize_dataset.py` - Reorganize Dataset (MOSE Format)
- **Function**: Split data into train/val/test according to MOSE dataset format using base site mapping, organized by site number level
- **Input**: `data/` directory containing images, labels, and RGB files
- **Output**: `dataset1/` directory structure in MOSE format

### 5. `print.py` - KML File Inspector
- **Function**: Inspect and print KML file structure and placemark information
- **Input**: `metadata/global_mining_extents_detailed.kml`
- **Output**: Console output showing KML structure

## Usage Steps

### Step 1: Generate Base Site Counts
```bash
cd misc
python count_images.py
```

### Step 2: Generate Ground Truth Labels
```bash
python create_gt.py
```

### Step 3: Generate RGB Visualizations
```bash
python generate_rgb.py
```

### Step 4: Reorganize Dataset (MOSE Format)
```bash
python reorganize_dataset.py
```

## Final Dataset Structure (MOSE Format)

```
dataset1/
├── train/
│   ├── images/
│   │   ├── mali_faleme_upper_1/
│   │   │   ├── 00000.tif
│   │   │   ├── 00001.tif
│   │   │   └── ...
│   │   ├── mali_faleme_upper_2/
│   │   │   ├── 00000.tif
│   │   │   ├── 00001.tif
│   │   │   └── ...
│   │   └── other_site_number/
│   ├── labels/
│   │   ├── mali_faleme_upper_1/
│   │   │   ├── 00000.png
│   │   │   ├── 00001.png
│   │   │   └── ...
│   │   ├── mali_faleme_upper_2/
│   │   │   ├── 00000.png
│   │   │   ├── 00001.png
│   │   │   └── ...
│   │   └── other_site_number/
│   └── rgb/
│       ├── mali_faleme_upper_1/
│       │   ├── 00000.png
│       │   ├── 00001.png
│       │   └── ...
│       ├── mali_faleme_upper_2/
│       │   ├── 00000.png
│       │   ├── 00001.png
│       │   └── ...
│       └── other_site_number/
├── val/
│   ├── images/
│   ├── labels/
│   └── rgb/
├── test/
│   ├── images/
│   ├── labels/
│   └── rgb/
└── filename_mapping.csv
```

## Dataset Statistics

Based on the MOSE dataset format split:
- **Total Images**: 5,800
- **Train**: 4,388 images (75.6%)
- **Val**: 960 images (16.6%)
- **Test**: 452 images (7.8%)

## Label Values

- **0**: Background
- **1**: Cloud
- **2**: Mining area

## Key Features

1. **Site Number Level Organization**: Files are organized by site number (e.g., `mali_faleme_upper_1`, `mali_faleme_upper_2`) rather than region level
2. **Sequential Numbering**: Files within each site folder are numbered sequentially (00000, 00001, 00002, etc.)
3. **Robust Base Site Matching**: Uses lowercase and stripped comparison for reliable site matching
4. **NDVI Vegetation Masking**: Automatically masks out vegetation areas (NDVI > 0.5) from mining labels
5. **Cloud Detection**: Uses band 8 for cloud masking
6. **Geometry Error Handling**: Automatically fixes geometry issues with buffer(0) operations
7. **MOSE Dataset Format**: Follows the official MOSE dataset split structure
8. **Filename Mapping**: Generates `filename_mapping.csv` to track original to new filename mappings

## Filename Mapping

The `filename_mapping.csv` file contains:
- `split`: train/val/test
- `site_number`: The site number folder name
- `original_filename`: Original filename from source data
- `new_filename`: New sequential filename (00000, 00001, etc.)
- `file_index`: Sequential index within the site folder

## Prerequisites

Ensure the following files exist:
- `metadata/global_mining_extents_detailed.kml`
- `metadata/image_file_metadata.csv`
- `mining_ndvi_timeseries/` directory with TIFF files

## Notes

- Scripts automatically create necessary directory structures
- Base site extraction handles various filename patterns with index suffixes
- The split mapping is based on the `base_site_counts.csv` file generated by `count_images.py`
- All scripts include error handling and progress reporting
- Files are organized at the site number level for proper MOSE format compliance 