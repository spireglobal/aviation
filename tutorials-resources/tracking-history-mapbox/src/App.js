import React, { useState, useEffect } from "react";
import MapGL, { Source, Layer, Marker } from "react-map-gl";
import { useDispatch, useSelector } from "react-redux";

import useInterval from "./hooks/useInterval";

import "mapbox-gl/dist/mapbox-gl.css";
import "./App.css";

const pointLayer = {
  type: "circle",
  id: "circle",
  paint: {
    "circle-radius": 2,
    "circle-color": "#007cbf",
  },
};

function parseResponse(response) {
  const results = [];
  response.split("\n").forEach((value) => {
    if (value) {
      try {
        const { target } = JSON.parse(value);
        results.push(target);
      } catch (error) {
        console.error(value);
      }
    }
  });
  return results;
}

function App() {
  const data = useSelector((state) => state.aircraft);
  const dispatch = useDispatch();
  const [animationIndex, setAnimationIndex] = useState(0);
  const [mode, setMode] = useState("plot");
  const [plot, setPlot] = useState(null);
  const [clickedPoint, setClickedPoint] = useState(null);
  const [viewport, setViewport] = useState({
    latitude: 0,
    longitude: -100,
    zoom: 3,
    bearing: 0,
    pitch: 0,
  });

  function getHistoryData(icao, start, end) {
    fetch(
      `https://api.airsafe.spire.com/v2/targets/history?icao_address=${icao}&start=${start}&end=${end}`,
      {
        headers: {
          Authorization: `Bearer rYWtOAD39fcF7V9JHaJ99n9RqMvSKyOo`,
        },
      }
    )
      .then(async (response) => {
        if (response.status === 401) {
          alert("Unauthorized");
        }
        response.text().then((r) => {
          dispatch({ type: "SET_AIRCRAFT_DATA", data: parseResponse(r) });
        });
      })
      .catch((e) => {
        alert("An error occured while calling the endpoint");
      });
  }

  useEffect(() => {
    getHistoryData(
      "398568",
      "2021-07-27T22:00:00.000Z",
      "2021-07-28T22:00:00.000Z"
    );
  }, []);

  useEffect(() => {
    if (data) {
      setPlot({
        type: "FeatureCollection",
        features: data.map((point) => ({
          type: "Feature",
          properties: {
            ...point,
          },
          geometry: {
            type: "Point",
            coordinates: [point.longitude, point.latitude],
          },
        })),
      });
      setViewport({
        latitude: data[0].latitude,
        longitude: data[0].longitude,
        zoom: 3,
        bearing: 0,
        pitch: 0,
      });
    }
  }, [data]);

  useInterval(
    () => {
      if (data[animationIndex + 1] && mode === "animation") {
        setAnimationIndex((prevIndex) => prevIndex + 1);
      }
    },
    mode === "animation" && data && data[animationIndex + 1] ? 10 : null
  );

  return (
    <div className="App">
      <div style={{ height: "500px" }}>
        <MapGL
          {...viewport}
          width="100%"
          height="100%"
          mapStyle="mapbox://styles/mapbox/outdoors-v11"
          onViewportChange={setViewport}
          mapboxApiAccessToken={
            // Please get yourself a mapbox token 
            // https://docs.mapbox.com/help/getting-started/access-tokens/
            "your_mapbox_token"
          }
          clickRadius={1}
          interactiveLayerIds={mode === "plot" && plot ? ["circle"] : null}
          onClick={(point) => {
            if (point?.features[0])
              setClickedPoint(point?.features[0].properties);
          }}
        >
          {mode === "plot" && plot && (
            <Source type="geojson" data={plot}>
              <Layer {...pointLayer} />
            </Source>
          )}
          {mode === "animation" && data && (
            <Marker
              key={`marker`}
              latitude={data[animationIndex].latitude}
              longitude={data[animationIndex].longitude}
              offsetLeft={-10}
              offsetTop={-10}
            >
              <svg
                fill="none"
                height={20}
                style={{
                  transformOrigin: "center",
                  transform: `rotate(${data[animationIndex].heading}deg)`,
                }}
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 12 12"
              >
                <path
                  d="M7.052 9.416c-.314-.055-.58-.11-.593-.123-.022-.022.127-.857.153-.857.025 0 .905.682.991.768.087.087.112.22.053.28-.018.017-.29-.013-.604-.068zm2.667-2.23c-.07-.029-.77-.36-1.553-.735a94.104 94.104 0 00-1.457-.69c-.018-.005-.032-.431-.032-.948v-.94l.154.12c.085.067.197.165.25.217.093.093.097.093.131.001.03-.08.055-.097.158-.112a.443.443 0 01.215.026c.083.04.093.07.094.312l.002.267.342.285.342.284.054-.08c.063-.095.256-.132.363-.07.053.032.072.106.077.306l.008.265.47.386c.26.213.495.425.524.472.057.095.074.6.022.653-.02.019-.093.01-.164-.019zM6.073 9.85c-.097 0-.157-.173-.281-.816a27.339 27.339 0 01-.161-.889c-.037-.272-.042-5.76-.006-6.09.042-.385.133-.646.275-.788.063-.063.141-.112.173-.108.178.022.332.247.416.613.055.239.084 5.859.033 6.325-.052.463-.3 1.638-.36 1.697-.03.03-.07.056-.089.056zm-.941-.439c-.368.064-.604.085-.632.057-.024-.025-.03-.093-.014-.152.027-.098.079-.145.535-.494.277-.212.511-.386.52-.386.008 0 .052.197.096.437l.081.437-.586.101zM3.93 6.481c-.843.401-1.557.734-1.586.74-.083.02-.1-.022-.111-.265-.016-.364.008-.399.568-.863l.482-.399.001-.238c.003-.275.07-.371.255-.365.092.003.138.026.183.093l.06.09.34-.278.34-.279.007-.268c.004-.147.026-.286.05-.31.05-.05.328-.056.376-.007a.24.24 0 01.048.097c.011.054.053.032.271-.143l.258-.206.003.935c.002.514 0 .936-.004.937l-1.54.73z"
                  fill="#0B0C10"
                />
              </svg>
            </Marker>
          )}
        </MapGL>
      </div>
      <button
        style={{ marginTop: "10px" }}
        onClick={() => {
          setClickedPoint(null);
          setAnimationIndex(0);
          setMode(mode === "plot" ? "animation" : "plot");
        }}
      >
        {mode === "plot" ? "Animation mode" : "Plot mode"}
      </button>
      {clickedPoint && (
        <div style={{ marginTop: "10px" }}>
          <div>
            <b>ICAO Address</b>: {clickedPoint.icao_address}
          </div>
          <div>
            <b>Altitude</b>: {clickedPoint.altitude_baro} ft.
          </div>
          <div>
            <b>Longitude</b>: {clickedPoint.longitude}
          </div>
          <div>
            <b>Latitude</b>: {clickedPoint.latitude}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
