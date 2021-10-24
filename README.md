## TopoJSON and GeoJSON for all Counties in US States Minified

This repo has all the TopoJSON and GeoJSON for all US States.

**Projection Size**

960x960

**How find the file you want**

`{state_name}`>`geo-county-min-topojson-#.json` (TopoJSON file)
`{state_name}`>`geo-county-min-#.json` (GeoJSON file)
example: `Alabama > geo-county-min-0.json` is  NAD83 / Alabama East (EPSG:26929) projection of Alabama counties 960x960

**What does the `#` represent?**

They represent the projection used on the json. Projections are referenced from `https://github.com/veltman/d3-stateplane`. The number is the position of the projection from top to bottom. For example, `0` is  NAD83 / Alabama East (EPSG:26929) 

