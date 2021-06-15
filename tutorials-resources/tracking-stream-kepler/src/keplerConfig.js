const dataFields = [
    {
      name: "timestamp",
      format: "YYYY-M-D:H:m:sZ",
      fieldIdx: 0,
      type: "timestamp",
      analyzerType: "TIME",
      valueAccessor: (values) => values[0],
    },
    { name: "icao_address", type: "string", analyzerType: "STRING" },
    { name: "longitude", type: "float", analyzerType: "FLOAT" },
    { name: "latitude", type: "float", analyzerType: "FLOAT" },
    { name: "altitude", type: "float", analyzerType: "FLOAT" },
    { name: "collection_type", type: "string", analyzerType: "STRING" },
    { name: "flight_number", type: "string", analyzerType: "STRING" },
    { name: "callsign", type: "string", analyzerType: "STRING" },
  ];
  
  const tooltipFields = [
    { name: "timestamp", format: null },
    { name: "latitude", format: null },
    { name: "longitude", format: null },
    { name: "altitude", format: null },
    { name: "icao_address", format: null },
    { name: "collection_type", format: null },
    { name: "flight_number", format: null },
    { name: "callsign", format: null },
  ];
  
  const initialConfig = {
    datasets: [
      {
        info: {
          label: "aircraft_satellite",
          id: "spire_aircraft_satellite",
        },
        data: {
          fields: dataFields,
          rows: [["", "", "", "", "", "", "", ""]],
        },
      },
      {
        info: {
          label: "aircraft_terrestrial",
          id: "spire_aircraft_terrestrial",
        },
        data: {
          fields: dataFields,
          rows: [["", "", "", "", "", "", "", ""]],
        },
      },
    ],
    config: {
      visState: {
        layers: [
          {
            type: "point",
            config: {
              dataId: "spire_aircraft_satellite",
              label: "aircraft_satellite",
              highlightColor: [255, 255, 255, 255],
              columns: {
                lat: "latitude",
                lng: "longitude",
                altitude: "altitude",
              },
              color: [210, 32, 32],
              visConfig: {
                radius: 10,
                fixedRadius: false,
                opacity: 1,
                outline: false,
                thickness: 2,
                filled: true,
              },
              isVisible: true,
            },
          },
          {
            type: "point",
            config: {
              dataId: "spire_aircraft_terrestrial",
              label: "aircraft_terrestrial",
              highlightColor: [255, 255, 255, 255],
              columns: {
                lat: "latitude",
                lng: "longitude",
                altitude: "altitude",
              },
              color: [48, 167, 172],
              visConfig: {
                radius: 10,
                fixedRadius: false,
                opacity: 1,
                outline: false,
                thickness: 2,
                filled: true,
              },
              isVisible: true,
            },
          },
        ],
        interactionConfig: {
          geocoder: false,
          tooltip: {
            fieldsToShow: {
              spire_aircraft_satellite: tooltipFields,
              spire_aircraft_terrestrial: tooltipFields,
            },
            compareMode: true,
            compareType: "absolute",
            enabled: true,
          },
        },
      },
    },
  };
  
  export { dataFields, initialConfig };
  