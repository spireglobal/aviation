import React, { useEffect } from "react";
import { addDataToMap } from "kepler.gl/actions";
import { useDispatch } from 'react-redux'
import KeplerGl from "kepler.gl";
import AutoSizer from "react-virtualized/dist/commonjs/AutoSizer";

import {dataFields, initialConfig} from './keplerConfig'
import "./App.css";

function extractJSON(string) {
  const results = string.match(/\{(?:[^{}])*\}/g);
  return results || [];
}

function App() {
  const dispatch = useDispatch()

  async function listenToStream() {
    dispatch(addDataToMap(initialConfig));
    fetch(
      `https://api.airsafe.spire.com/v2/targets/stream?compression=none&late_filter=true`,
      {
        headers: {
          Authorization: `Bearer your_api_token`,
        },
      }
    )
      .then(async (response) => {
        if (response.status === 401) {
          alert("Unauthorized");
        }

        const stream = response.body.getReader();
        const currentData = {
          satellite: [["", "", "", "", "", "", "", ""]],
          terrestrial: [["", "", "", "", "", "", "", ""]],
        };
        while (true) {
          const { value, done } = await stream.read();
          if (done) {
            break;
          }
          try {
            extractJSON(new TextDecoder("utf-8").decode(value)).forEach(
              (parsed) => {
                if (parsed.indexOf("icao_address") > 0) {
                  const elem = JSON.parse(parsed);
                  const index = currentData[elem.collection_type].findIndex(
                    (item) => item[1] === elem.icao_address
                  );
                  const newElem = [
                    elem.timestamp || "",
                    elem.icao_address || "",
                    elem.longitude || "",
                    elem.latitude || "",
                    elem.altitude_baro || "",
                    elem.collection_type || "",
                    elem.flight_number || "",
                    elem.callsign || "",
                  ];
                  if (index >= 0) {
                    currentData[elem.collection_type][index] = newElem;
                  } else {
                    currentData[elem.collection_type].push(newElem);
                  }
                }
              },
              []
            );
            if (
              currentData.satellite.length > 0 ||
              currentData.terrestrial.length > 0
            ) {
              dispatch(addDataToMap({
                datasets: [
                  {
                    info: {
                      label: "aircraft_satellite",
                      id: "spire_aircraft_satellite",
                    },
                    data: {
                      fields: dataFields,
                      rows: currentData.satellite,
                    },
                  },
                  {
                    info: {
                      label: "aircraft_terrestrial",
                      id: "spire_aircraft_terrestrial",
                    },
                    data: {
                      fields: dataFields,
                      rows: currentData.terrestrial,
                    },
                  },
                ],
              }));
            }
          } catch (e) {
            alert("An error occured while parsing stream results");
          }
        }
      })
      .catch((e) => {
        alert("An error occured while calling the endpoint");
      });
  }

  useEffect(() => {
    listenToStream()
  }, []);

  return (
    <div className="App">
        <div style={{ height: "100vh" }}>
          <AutoSizer>
            {({ height, width }) => (
              <KeplerGl
                id="kepler-gl-tutorial"
                mapboxAccessToken={
                  // Please get yourself a mapbox token 
                  // https://docs.mapbox.com/help/getting-started/access-tokens/
                  "your_mapbox_token"
                }
                width={width}
                height={height}
                theme={{ tooltipBg: "#1869b5", tooltipColor: "#ffffff" }}
              />
            )}
          </AutoSizer>
        </div>
    </div>
  );
}

export default App;
