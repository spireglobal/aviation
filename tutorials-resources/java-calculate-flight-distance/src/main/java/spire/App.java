package spire;

import java.net.URISyntaxException;
import java.util.concurrent.ExecutionException;
import java.io.IOException;
import java.util.Optional;
import java.net.URI;
import org.json.JSONObject;
import java.net.http.HttpResponse;
import java.net.http.HttpRequest;
import org.apache.http.client.utils.URIBuilder;
import java.net.http.HttpClient;

class App
{
    public static void main(final String[] args) throws IOException, InterruptedException, ExecutionException, URISyntaxException {
        HttpClient client = HttpClient.newHttpClient();
        URI uri = new URIBuilder("https://api.airsafe.spire.com/v2/targets/history")
                .addParameter("start", "2021-04-20T12:00:00Z").addParameter("end", "2021-04-20T18:30:00Z")
                .addParameter("longitude_between", "2.481443,2.642431")
                .addParameter("latitude_between", "48.970752,49.041694").build();
        HttpRequest request = HttpRequest.newBuilder().uri(uri).header("Authorization", "Bearer <your_token>").build();
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        Optional<String> test = response.body().lines().filter(line -> {
            JSONObject obj = new JSONObject(line);
            try {
                JSONObject target = obj.getJSONObject("target");
                return target.getString("arrival_airport_iata").equals("CDG") && target.getString("departure_airport_iata").equals("LHR");
            }
            catch (Exception e) {
                return false;
            }
        }).findFirst();

        Flight flight = new Flight(test);
        flight.getFlightData();
        flight.calculateFlightDistance();
        flight.getFlightCountries();
    }
}