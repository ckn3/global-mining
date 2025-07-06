import os
import shutil
import random
import re
import pandas as pd
from pathlib import Path
import glob

def create_dataset_structure():
    """Create the dataset directory structure in MOSE format"""
    os.makedirs("dataset1", exist_ok=True)
    for split in ["train", "val", "test"]:
        os.makedirs(f"dataset1/{split}", exist_ok=True)
        os.makedirs(f"dataset1/{split}/images", exist_ok=True)
        os.makedirs(f"dataset1/{split}/labels", exist_ok=True)
        os.makedirs(f"dataset1/{split}/rgb", exist_ok=True)

def get_image_files():
    """Get all image files from data/images"""
    image_files = glob.glob("data/images/*.tif")
    return sorted(image_files)

def load_split_mapping():
    """Load split mapping from base_site_counts.csv, lowercased and stripped for robust matching"""
    csv_path = "/deac/csc/alqahtaniGrp/cuij/global-mining/misc/base_site_counts.csv"
    df = pd.read_csv(csv_path)
    split_mapping = {}
    for _, row in df.iterrows():
        split_mapping[row['base_site'].strip().lower()] = row['split'].strip().lower()
    return split_mapping

def get_base_site_from_filename(filename, split_mapping):
    """Extract base site from filename, lowercased and stripped"""
    name = filename.replace('.tif', '').replace('Landsat_Image_', '')
    base_site = re.sub(r'_\d+_\d{8}$', '', name)
    if base_site == name:
        base_site = re.sub(r'_\d+$', '', name)
    base_site = base_site.strip().lower()
    if base_site in split_mapping:
        return base_site
    return None

def split_dataset_by_site(image_files, split_mapping):
    """Split dataset based on site information from base_site_counts.csv"""
    train_files = []
    val_files = []
    test_files = []
    unmatched = 0
    
    print("\n=== Splitting dataset by site ===")
    
    for image_path in image_files:
        filename = os.path.basename(image_path)
        base_site = get_base_site_from_filename(filename, split_mapping)
        
        if base_site and base_site in split_mapping:
            split = split_mapping[base_site]
            if split == 'train':
                train_files.append(image_path)
            elif split == 'val':
                val_files.append(image_path)
            elif split == 'test':
                test_files.append(image_path)
            print(f"  {filename} -> {base_site} -> {split}")
        else:
            train_files.append(image_path)
            unmatched += 1
            print(f"  {filename} -> unknown site -> train (default)")
    
    return train_files, val_files, test_files, unmatched

def organize_files_by_site(file_list, split_name):
    """Organize files by site number with sequential numbering in MOSE format"""
    print(f"\n=== Organizing files for {split_name} split ===")
    
    # Group files by site number (not base site)
    site_files = {}
    for image_path in file_list:
        filename = os.path.basename(image_path)
        base_name = os.path.splitext(filename)[0]
        
        # Extract site number from filename (e.g., mali_faleme_upper_1_20200524 -> mali_faleme_upper_1)
        name = base_name.replace('Landsat_Image_', '')
        # Remove date suffix first, then extract site number
        site_number = re.sub(r'_\d{8}$', '', name)
        
        if site_number not in site_files:
            site_files[site_number] = []
        site_files[site_number].append(image_path)
    
    # Create filename mapping data
    mapping_data = []
    
    # Process each site number
    for site_number, image_paths in site_files.items():
        print(f"\nProcessing site: {site_number}")
        
        # Create site directory
        site_dir = f"dataset1/{split_name}/images/{site_number}"
        os.makedirs(site_dir, exist_ok=True)
        
        # Sort files to ensure consistent ordering
        image_paths.sort()
        
        # Copy files with sequential numbering
        for idx, image_path in enumerate(image_paths):
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            
            # Source paths
            label_path = os.path.join("data/labels", f"{base_name}.png")
            rgb_path = os.path.join("data/rgb", f"{base_name}.png")
            
            # Destination paths with sequential numbering
            new_filename = f"{idx:05d}"  # 00000, 00001, etc.
            dst_image = os.path.join(site_dir, f"{new_filename}.tif")
            dst_label = os.path.join(f"dataset1/{split_name}/labels/{site_number}", f"{new_filename}.png")
            dst_rgb = os.path.join(f"dataset1/{split_name}/rgb/{site_number}", f"{new_filename}.png")
            
            # Create label and rgb directories
            os.makedirs(os.path.dirname(dst_label), exist_ok=True)
            os.makedirs(os.path.dirname(dst_rgb), exist_ok=True)
            
            # Copy files
            if os.path.exists(image_path):
                shutil.copy2(image_path, dst_image)
                print(f"✅ Copied image: {base_name}.tif -> {new_filename}.tif")
            else:
                print(f"❌ Image not found: {image_path}")
                
            if os.path.exists(label_path):
                shutil.copy2(label_path, dst_label)
                print(f"✅ Copied label: {base_name}.png -> {new_filename}.png")
            else:
                print(f"❌ Label not found: {label_path}")
                
            if os.path.exists(rgb_path):
                shutil.copy2(rgb_path, dst_rgb)
                print(f"✅ Copied RGB: {base_name}.png -> {new_filename}.png")
            else:
                print(f"❌ RGB not found: {rgb_path}")
            
            # Add to mapping data
            mapping_data.append({
                'split': split_name,
                'site_number': site_number,
                'original_filename': base_name,
                'new_filename': new_filename,
                'file_index': idx
            })
    
    return mapping_data

def save_filename_mapping(all_mapping_data):
    """Save filename mapping to CSV"""
    df = pd.DataFrame(all_mapping_data)
    mapping_path = "dataset1/filename_mapping.csv"
    df.to_csv(mapping_path, index=False)
    print(f"\n✅ Filename mapping saved to: {mapping_path}")
    print(f"Total mappings: {len(df)}")

def main():
    print("=== Dataset Reorganization (MOSE Format) ===")
    
    random.seed(42)
    create_dataset_structure()
    
    split_mapping = load_split_mapping()
    print(f"Loaded split mapping for {len(split_mapping)} sites")
    
    image_files = get_image_files()
    print(f"\nFound {len(image_files)} images")
    
    if len(image_files) == 0:
        print("❌ No images found in data/images/")
        return
    
    train_files, val_files, test_files, unmatched = split_dataset_by_site(image_files, split_mapping)
    
    print(f"\nDataset split by site:")
    print(f"  Train: {len(train_files)} images")
    print(f"  Val: {len(val_files)} images")
    print(f"  Test: {len(test_files)} images")
    print(f"  Unmatched (defaulted to train): {unmatched}")
    print(f"  Total: {len(train_files) + len(val_files) + len(test_files)}")
    
    # Organize files in MOSE format
    all_mapping_data = []
    
    train_mapping = organize_files_by_site(train_files, "train")
    all_mapping_data.extend(train_mapping)
    
    val_mapping = organize_files_by_site(val_files, "val")
    all_mapping_data.extend(val_mapping)
    
    test_mapping = organize_files_by_site(test_files, "test")
    all_mapping_data.extend(test_mapping)
    
    # Save filename mapping
    save_filename_mapping(all_mapping_data)
    
    print("\n=== Dataset reorganization completed! ===")
    print("Dataset organized in MOSE format with sequential numbering")

if __name__ == "__main__":
    main() 