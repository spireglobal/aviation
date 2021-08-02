import { combineReducers } from "redux";
import { configureStore } from "@reduxjs/toolkit";

import aircraftReducer from "../reducers/aircraftReducer";

export const store = configureStore({
  reducer: combineReducers({ aircraft: aircraftReducer }),
});
