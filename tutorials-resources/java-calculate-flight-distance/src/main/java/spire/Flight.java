package spire;

import java.util.List;
import java.util.HashSet;
import java.util.ListIterator;
import java.net.URISyntaxException;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpResponse;
import java.net.http.HttpRequest;
import org.apache.http.client.utils.URIBuilder;
import java.net.http.HttpClient;
import java.util.Optional;
import org.json.JSONObject;
import java.util.ArrayList;

public class Flight
{
    private ArrayList<JSONObject> flightPath;
    private JSONObject targetUpdate;
    
    public Flight(Optional<String> targetUpdateString) {
        this.targetUpdate = new JSONObject((String)targetUpdateString.get()).getJSONObject("target");
    }
    
    public ArrayList<JSONObject> getFlightData() throws IOException, InterruptedException, URISyntaxException {
        HttpClient client = HttpClient.newHttpClient();
        URI uri = new URIBuilder("https://api.airsafe.spire.com/v2/targets/history").addParameter("start", this.targetUpdate.getString("departure_scheduled_time")).addParameter("end", this.targetUpdate.getString("arrival_scheduled_time")).addParameter("icao_address", this.targetUpdate.getString("icao_address")).build();
        HttpRequest request = HttpRequest.newBuilder().uri(uri).header("Authorization", "Bearer <your_token>").build();
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        ArrayList<JSONObject> flightPath = new ArrayList<JSONObject>();
        response.body().lines().forEach(line -> {
            JSONObject obj = new JSONObject(line);
            try {
                JSONObject target = obj.getJSONObject("target");
                flightPath.add(target);
            }
            catch (Exception ex) {}
            return;
        });
        return this.flightPath = flightPath;
    }
    
    public double calculateFlightDistance() {
        ListIterator<JSONObject> it = this.flightPath.listIterator();
        double totalDist = 0.0;
        while (it.hasNext()) {
            JSONObject current = it.next();
            JSONObject next = it.hasNext() ? it.next() : null;
            if (next != null) {
                it.previous();
                double theta = current.getDouble("longitude") - next.getDouble("longitude");
                double dist = Math.sin(Math.toRadians(current.getDouble("latitude"))) * Math.sin(Math.toRadians(next.getDouble("latitude"))) + Math.cos(Math.toRadians(current.getDouble("latitude"))) * Math.cos(Math.toRadians(next.getDouble("latitude"))) * Math.cos(Math.toRadians(theta));
                dist = Math.acos(dist);
                dist = Math.toDegrees(dist);
                dist = dist * 60.0 * 1.1515;
                dist *= 1.609344;
                totalDist += dist;
            }
        }
        System.out.println(String.valueOf(this.flightPath.size()) + " datapoints found");
        System.out.println(String.valueOf(totalDist) + " kms");
        return totalDist;
    }
    
    public ArrayList<String> getFlightCountries() {
        ArrayList<String> cities = new ArrayList<String>();
        this.flightPath.forEach(point -> {
            atlas.City city = new atlas.Atlas().find(point.getDouble("latitude"), point.getDouble("longitude"));
            if (city != null) {
                cities.add(city.countryCode);
            }
            return;
        });
        List<String> newList = new ArrayList<String>(new HashSet<String>(cities));
        System.out.println("Countries flown over " + newList);
        return cities;
    }
}
