import os
from bs4 import BeautifulSoup
import requests
import requests
import pprint
from bs4 import BeautifulSoup
import json

def get_projections():
    state_plane_readme_html_req = requests.get('https://github.com/veltman/d3-stateplane')
    html = state_plane_readme_html_req.text

    # html parser
    soup = BeautifulSoup(html, 'html.parser')
    readme_content = soup.find_all(attrs={"data-target": 'readme-toc.content'})[0]
    state_planes = readme_content.article.find_all(recursive=False)[3:]
    projections = []
    for i in range(0, len(state_planes), 2):
        projection = state_planes[i+1].text.replace('var projection = ', '').replace('\n','').replace(' ', '').replace(';','')
        projections.append((state_planes[i].text, projection))
    return projections

def download_shape_files():
    year = 2019

    # get all states
    all_states = get_all_states()

    # associate states with projections
    projections = get_projections()
    merged_projections = merge_projection_states(projections, all_states)

    already_downloaded = set()
    for row in merged_projections:
        name = row[0]
        if name not in already_downloaded:
            already_downloaded.add(name)
            fips = row[1]
            new_name = name.replace(' ', '')
            os.system(f'mkdir {new_name}')
            os.system(f'cd {new_name} && curl "https://www2.census.gov/geo/tiger/GENZ{year}/shp/cb_{year}_{fips}_tract_500k.zip" -o {new_name}-tract.zip')
            os.system(f'cd {new_name} && unzip {new_name}-tract.zip')

def create_topojson_and_geojson():
    year = 2019

    # get all states
    all_states = get_all_states()

    # associate states with projections
    projections = get_projections()
    merged_projections = merge_projection_states(projections, all_states)

    for i, row in enumerate(merged_projections):
        name = row[0]
        new_name = name.replace(' ', '')
        print(f'processing {new_name}')
        fips = row[1]
        projection = row[3]

        outpath = lambda file_name : f'{new_name}/{file_name}'

        # start geo data unoptimized
        os.system(f'cd {new_name} && npx shp2json cb_{year}_{fips}_tract_500k.shp -o geoData.json')

        # get albers
        os.system(f'geoproject "{projection}.fitSize([960, 960], d)" < {outpath("geoData.json")} > {outpath("geo-albers.json")}')

        os.system('''
            ndjson-split 'd.features' \
                < %s \
                > %s
        ''' % (outpath("geo-albers.json"), outpath("geo-albers.ndjson")))

        os.system('''
            ndjson-map 'd.id = d.properties.GEOID.slice(0, 5), d' \
                < %s \
                > %s
        ''' % (outpath("geo-albers.ndjson"), outpath("geo-albers-id.ndjson")))

        os.system('''
            ndjson-reduce \
                < %s \
                | ndjson-map '{type: "FeatureCollection", features: d}' \
                > %s
        ''' % (outpath("geo-albers-id.ndjson"), outpath("geo-albers.json")))

        os.system('''
            npx ndjson-split 'd.features' \
                < %s \
                > %s
        ''' % (outpath("geo-albers.json"), outpath("geo-albers.ndjson")))

        os.system('''
            geo2topo -n \
                tracts=%s \
                > %s
            ''' % (outpath("geo-albers.ndjson"), outpath("geo-tracts-topo.json"))
        )

        os.system('''
            toposimplify -p 1 -f \
                < %s \
                > %s
        ''' % (outpath("geo-tracts-topo.json"), outpath("geo-simple-topo.json")))

        os.system('''
            topoquantize 1e5 \
                < %s \
                > %s
        ''' % (outpath("geo-simple-topo.json"),outpath("geo-quantized-topo.json")))

        os.system('''
            topomerge -k 'd.id' counties=tracts \
                < %s \
                > %s
        ''' % (outpath("geo-quantized-topo.json"), outpath(f'geo-county-min-topojson-{i}.json')))

        os.system('''
            topo2geo counties=- \
                < %s > %s
        ''' % (outpath(f'geo-county-min-topojson-{i}.json'), outpath(f'geo-county-min-{i}.json')))

def get_all_states():
    state_names = []
    with open('state-fips.csv', 'r') as state_file:
        for line in state_file:
            state_data = line.replace('\n','').split(',')
            fips = state_data[3] if len(state_data[3]) == 2 else f'0{state_data[3]}'
            state_names.append((state_data[0], fips))
    return state_names

def merge_projection_states(projections, all_states):
    merged_projections = []
    for state in all_states:
        for projection in projections:
            if state[0] in projection[0]:
                merged_projections.append([state[0], state[1], projection[0], projection[1]])
    return merged_projections

def get_merged_projections():
    # get all states
    all_states = get_all_states()

    # associate states with projections
    projections = get_projections()
    return merge_projection_states(projections, all_states)

def add_projection_feature():
    merged_projections = get_merged_projections()
    for i, row in enumerate(merged_projections):
        # get columns
        name = row[0]
        new_name = name.replace(' ', '')
        projection_name = row[2]
        fips = row[1]
        projection = row[3]

        # helper for path consolidation
        outpath = lambda x : f'{new_name}/{x}'

        # get geoData (geo-county-min-#.json)
        with open(outpath(f'geo-county-min-{i}.json'), 'r') as geo_data_file:
            geo_data_json = json.loads(geo_data_file.read())
            geo_data_json['metadata'] = {
                'name': name,
                'projection_name': projection_name,
                'fips': fips,
                'd3_projection': projection
            }
            geo_data_temp_copy = open(outpath(f'geo-county-min-{i}-copy.json'), 'w')
            geo_data_temp_copy.write(json.dumps(geo_data_json))

            old_json = outpath(f"geo-county-min-{i}.json")
            os.system(f'rm {old_json}')
            new_json = outpath(f'geo-county-min-{i}-copy.json')
            os.system(f'mv {new_json} {old_json}')

if __name__ == '__main__':
    # create_topojson_and_geojson()
    # download_shape_files()
    # add_projection_feature()
