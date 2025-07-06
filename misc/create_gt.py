import rasterio
from rasterio.features import rasterize
from shapely.geometry import Polygon, shape, box
from shapely.ops import transform
from xml.etree import ElementTree as ET
import numpy as np
import pyproj
import os
import shutil
import re
import pandas as pd
from shapely.errors import GEOSException
import matplotlib.pyplot as plt

# File paths
kml_path = "metadata/global_mining_extents_detailed.kml"
metadata_path = "metadata/image_file_metadata.csv"

# Read metadata CSV
df = pd.read_csv(metadata_path)
print(f"\n=== Processing {len(df)} images ===")

# Create output directories if they don't exist
os.makedirs("data/images", exist_ok=True)
os.makedirs("data/labels", exist_ok=True)

# Dictionary to store generated labels
base_mask_cache = {}  # Cache for base mining masks by site_no

def calculate_ndvi_mask(image_path):
    """Calculate NDVI mask where NDVI > 0.5 (vegetation)"""
    with rasterio.open(image_path) as src:
        # Read B4 (NIR) and B3 (Red) bands
        b4 = src.read(4).astype(np.float32)  # NIR band
        b3 = src.read(3).astype(np.float32)  # Red band
        
        # Calculate NDVI
        denominator = b4 + b3
        # Avoid division by zero
        denominator[denominator == 0] = 1e-6
        ndvi = (b4 - b3) / denominator
        
        # Create mask where NDVI > 0.5 (vegetation)
        vegetation_mask = ndvi > 0.5
        
        return vegetation_mask

def generate_base_mask(polygons, image_shape, image_transform):
    """Generate base mining mask from polygons"""
    return rasterize(
        [(geom, 2) for geom in polygons],  # Changed from 255 to 2 for mining class
        out_shape=image_shape,
        transform=image_transform,
        fill=0,
        dtype='uint8'
    )

def get_polygons_for_site(base_site_no, image_bounds, image_crs):
    """Get polygons for a specific site"""
    # Setup CRS transformer from EPSG:4326 (KML) to image CRS
    project = pyproj.Transformer.from_crs("EPSG:4326", image_crs, always_xy=True).transform
    
    # Create image bounding box in the image's CRS
    image_box = box(*image_bounds)
    
    # Read KML and reproject polygons
    tree = ET.parse(kml_path)
    root = tree.getroot()
    ns = {"kml": "http://www.opengis.net/kml/2.2"}
    
    polygons = []
    total_polygons = 0
    matched_polygons = 0
    
    print("\n=== Polygon Checks ===")
    for pm in root.findall(".//kml:Placemark", ns):
        name_elem = pm.find(".//kml:name", ns)
        if name_elem is not None:
            # Remove index suffix from polygon name for comparison
            poly_name = re.sub(r'_\d+$', '', name_elem.text)
            if base_site_no.lower() in poly_name.lower():
                coords_elem = pm.find(".//kml:coordinates", ns)
                if coords_elem is not None:
                    coords_text = coords_elem.text.strip()
                    coords = [tuple(map(float, pt.split(",")[:2])) for pt in coords_text.split()]
                    poly_wgs84 = Polygon(coords)
                    poly_projected = transform(project, poly_wgs84)  # Reproject to image CRS
    
                    total_polygons += 1
                    poly_bounds = poly_projected.bounds
                    intersects = poly_projected.intersects(image_box)
                    print(f"Polygon {total_polygons} ({name_elem.text}): Bounds {poly_bounds} | Intersects Image: {intersects}")
                    if intersects:
                        try:
                            # Try to calculate intersection
                            intersection = poly_projected.intersection(image_box)
                        except GEOSException:
                            print(f"  ⚠️ Compilation error, trying to fix with buffer(0)...")
                            try:
                                # Fix geometry problem with buffer(0)
                                intersection = poly_projected.buffer(0).intersection(image_box.buffer(0))
                            except GEOSException as e:
                                print(f"  ❌ Cannot fix geometry problem: {str(e)}")
                                continue
                        
                        if not intersection.is_empty:
                            polygons.append(intersection)
                            matched_polygons += 1
    
    print(f"\nTotal polygons in KML: {total_polygons}")
    print(f"Polygons matching base site_no '{base_site_no}': {matched_polygons}")
    print(f"Polygons intersecting the image: {len(polygons)}")
    
    return polygons

# Process each image
for _, row in df.iterrows():
    image_id = row['image_id']
    site_no = row['site_no']
    
    # Remove index suffix from site_no (e.g., _TSTM_2 -> _TSTM)
    base_site_no = re.sub(r'_\d+$', '', site_no)
    
    print(f"\n=== Processing Image ===")
    print(f"Image ID: {image_id}")
    print(f"Site No: {site_no}")
    print(f"Base Site No (for polygon search): {base_site_no}")
    
    # Set image path
    image_path = os.path.join("mining_ndvi_timeseries", image_id)
    
    # Get image filename without path and prefix
    output_image_filename = image_id.replace("Landsat_Image_", "")
    output_label_filename = output_image_filename.replace(".tif", ".png")  # Change extension to .png
    
    # Set output paths
    output_image_path = os.path.join("data/images", output_image_filename)
    output_label_path = os.path.join("data/labels", output_label_filename)
    
    # Copy only first 7 bands of the original image
    with rasterio.open(image_path) as src:
        # Read metadata from source
        meta = src.meta.copy()
        # Update metadata for 7 bands
        meta.update(count=7)
        
        # Read first 7 bands and write to new file
        with rasterio.open(output_image_path, 'w', **meta) as dst:
            for i in range(1, 8):
                dst.write(src.read(i), i)
    
    print(f"✅ Image (7 bands) copied to {output_image_path}")
    
    # Load image to get bounds and transform
    with rasterio.open(image_path) as src:
        image_bounds = src.bounds
        image_crs = src.crs
        image_transform = src.transform
        image_shape = (src.height, src.width)
        
        # Read cloud mask (8th band)
        cloud_mask = src.read(8).astype(np.uint8)
    
    print("\n=== Image Metadata ===")
    print(f"CRS: {image_crs}")
    print(f"Bounds:\n  Left: {image_bounds.left}\n  Bottom: {image_bounds.bottom}\n  Right: {image_bounds.right}\n  Top: {image_bounds.top}")
    print(f"Image size (HxW): {image_shape}\n")
    
    # Get or generate base mask for this site
    if site_no in base_mask_cache:
        print(f"📋 Using cached base mask for {site_no}")
        mask = base_mask_cache[site_no].copy()  # Make a copy to avoid modifying the cached mask
    else:
        print(f"🔄 Generating new base mask for {site_no}")
        polygons = get_polygons_for_site(base_site_no, image_bounds, image_crs)
        mask = generate_base_mask(polygons, image_shape, image_transform)
        base_mask_cache[site_no] = mask.copy()  # Cache a copy of the mask
    
    # Calculate NDVI mask and apply it to the mining mask
    print("\n=== Calculating NDVI mask ===")
    vegetation_mask = calculate_ndvi_mask(image_path)
    # Set mining areas that are vegetation (NDVI > 0.5) to background
    mask[vegetation_mask] = 0
    
    # Combine masks with priority: cloud (1) > mining (2) > background (0)
    final_mask = np.zeros_like(mask)
    final_mask[cloud_mask == 1] = 1  # Set cloud pixels to 1
    final_mask[(mask == 2) & (cloud_mask != 1)] = 2  # Set mining pixels to 2 where not cloud
    
    # Save label as PNG with original values (0,1,2)
    plt.imsave(output_label_path, final_mask, cmap='viridis', vmin=0, vmax=2)
    
    print(f"✅ Label image saved to {output_label_path}")
    print("="*50)

print("\nDataset generation completed!") 