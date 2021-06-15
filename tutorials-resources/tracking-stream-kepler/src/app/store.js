import {createStore, combineReducers, applyMiddleware, compose} from 'redux';
import keplerGlReducer, { uiStateUpdaters } from "kepler.gl/reducers";
import {enhanceReduxMiddleware} from 'kepler.gl/middleware';

const initialState = {};
const reducers = combineReducers({
  keplerGl: keplerGlReducer.initialState({
    mapStyle: {
      styleType: "light",
    },
    uiState: {
      readOnly: true,
      currentModal: null,
      mapControls: {
        ...uiStateUpdaters.DEFAULT_MAP_CONTROLS,
        visibleLayers: {
          show: false,
        },
        mapLegend: {
          show: true,
          active: false,
        },
        toggle3d: {
          show: true,
        },
        splitMap: {
          show: false,
        },
        mapDraw: {
          show: false,
        },
        mapLocale: {
          show: false,
        },
      },
    },
  }),
});

// using enhancers
const middlewares = enhanceReduxMiddleware([
  // Add other middlewares here
]);
const enhancers = [applyMiddleware(...middlewares)];

export const store =  createStore(reducers, initialState, compose(...enhancers));