import pandas as pd
import re
from collections import defaultdict

# Read metadata CSV file
metadata_path = "metadata/image_file_metadata.csv"
df = pd.read_csv(metadata_path)

# Define country and continent mapping
location_info = {
    'nicaragua': {'country': 'Nicaragua', 'continent': 'North America'},
    'peru': {'country': 'Peru', 'continent': 'South America'},
    'russia': {'country': 'Russia', 'continent': 'Asia'},
    'mozambique': {'country': 'Mozambique', 'continent': 'Africa'},
    'french_guiana': {'country': 'French Guiana', 'continent': 'South America'},
    'cameroon': {'country': 'Cameroon', 'continent': 'Africa'},
    'myanmar': {'country': 'Myanmar', 'continent': 'Asia'},
    'drc': {'country': 'Democratic Republic of the Congo', 'continent': 'Africa'},
    'mali': {'country': 'Mali', 'continent': 'Africa'},
    'mongolia': {'country': 'Mongolia', 'continent': 'Asia'},
    'nigeria': {'country': 'Nigeria', 'continent': 'Africa'},
    'senegal': {'country': 'Senegal', 'continent': 'Africa'},
    'indonesia': {'country': 'Indonesia', 'continent': 'Asia'},
    'sierra_leone': {'country': 'Sierra Leone', 'continent': 'Africa'},
    'venezuela': {'country': 'Venezuela', 'continent': 'South America'},
    'phillipines': {'country': 'Philippines', 'continent': 'Asia'}
}

# Define split mapping
split_info = {
    'cameroon_kadei_river_batouri_agm_region': 'train',
    'drc_lindi_river_upper_agm_region': 'val',
    'mali_faleme_upper': 'train',
    'mozambique_manica_TSTM': 'train',
    'nigeria_ijesa_agm_region_TSTM': 'val',
    'senegal_river_gambie_agm_region_TSTM': 'test',
    'sierra_leone_pampan_river_gold_diamond_region': 'test',
    'indonesia_madreng_agm_region': 'train',
    'indonesia_kulu_agm_region': 'val',
    'indonesia_batang_hari_bedaro_agm_region': 'train',
    'indonesia_west_kalimantan_selimbau_agm_region_TSTM': 'train',
    'mongolia_gatsuurt_agm_region': 'test',
    'myanmar_chindwin_river_hkamti_agm_region': 'train',
    'myanmar_chindwin_river_ningbyen_agm_region': 'train',
    'myanmar_namsi_awng_agm_region': 'train',
    'myanmar_theinkun_agm_region': 'train',
    'myanmar_kawbyin_agm_region_TSTM': 'train',
    'myanmar_maw_luu_agm_region': 'val',
    'phillipines_quiniput_downstream_agm_region_TSTM': 'test',
    'russia_mongolia_border_agm_region': 'val',
    'russia_novotroitsk_agm_region_TSTM': 'train',
    'russia_tumnin_agm_region_TSTM': 'train',
    'russia_koryak_plateau': 'train',
    'russia_tumnin_tributary_agm_region_TSTM': 'train',
    'russia_edakuy_agm_region_TSTM': 'train',
    'nicaragua_somotillo_agm_region': 'test',
    'french_guiana_deux_branches_agm_region_TSTM': 'test',
    'peru_la_pampa_south_agm_region': 'train',
    'peru_rio_quimiri_downstream': 'val',
    'peru_la_pampa_north_agm_region': 'train',
    'peru_rio_inambari_channel_agm_region': 'train',
    'peru_tournavista_agm_region_TSTM': 'train',
    'venezuela_yapacana_south_agm_region_TSTM': 'test'
}

# Create counter for base sites
base_site_counts = defaultdict(int)

# Count images for each base site
for site_no in df['site_no']:
    # Remove index suffix (e.g., _TSTM_2 -> _TSTM)
    base_site_no = re.sub(r'_\d+$', '', site_no)
    base_site_counts[base_site_no] += 1

# Create DataFrame with counts
results_df = pd.DataFrame({
    'base_site': list(base_site_counts.keys()),
    'image_count': list(base_site_counts.values())
})

# Add location information
def get_location_info(base_site):
    for key, info in location_info.items():
        if key in base_site.lower():
            return info['country'], info['continent']
    return 'Unknown', 'Unknown'

results_df[['country', 'continent']] = results_df['base_site'].apply(get_location_info).apply(pd.Series)

# Add split information
results_df['split'] = results_df['base_site'].map(split_info)

# Sort by continent, country, and image count
results_df = results_df.sort_values(['continent', 'country', 'image_count'], ascending=[True, True, False])

# Print results
print("\n=== Number of images per base site ===")
for _, row in results_df.iterrows():
    print(f"{row['base_site']}: {row['image_count']} images ({row['split']})")

# Print summary
print(f"\nSummary:")
print(f"Number of unique base sites: {len(base_site_counts)}")
print(f"Total number of images: {len(df)}")

# Print summary by continent
print("\n=== Summary by Continent ===")
continent_summary = results_df.groupby('continent').agg({
    'base_site': 'count',
    'image_count': 'sum'
}).rename(columns={'base_site': 'number_of_sites'})
print(continent_summary)

# Print summary by country
print("\n=== Summary by Country ===")
country_summary = results_df.groupby(['continent', 'country']).agg({
    'base_site': 'count',
    'image_count': 'sum'
}).rename(columns={'base_site': 'number_of_sites'})
print(country_summary)

# Print summary by split
print("\n=== Summary by Split ===")
split_summary = results_df.groupby('split').agg({
    'base_site': 'count',
    'image_count': 'sum'
}).rename(columns={'base_site': 'number_of_sites'})
print(split_summary)

# Save results to CSV
results_df.to_csv("misc/base_site_counts.csv", index=False)
print("\nResults saved to misc/base_site_counts.csv") 