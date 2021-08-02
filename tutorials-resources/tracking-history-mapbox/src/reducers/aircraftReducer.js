export default function aircraftReducer(state = null, action) {
  switch (action.type) {
    case "SET_AIRCRAFT_DATA":
      return action.data;
    default:
      return state;
  }
}
