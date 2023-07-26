package com.example;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;

/**
 * Hello world!
 */
public class App {
    public static void main(String[] args) {
        String url = "https://www.google.com";

        while (true) {
            try {
                // Create a URL object representing the target URL
                URL obj = new URL(url);

                // Open a connection to the URL
                HttpURLConnection connection = (HttpURLConnection) obj.openConnection();

                // Set the request method to GET
                connection.setRequestMethod("GET");

                // Get the response code
                int responseCode = connection.getResponseCode();

                System.out.println("Sending GET request to URL: " + url);
                System.out.println("Response Code: " + responseCode);

                // Read the response from the server
                BufferedReader in = new BufferedReader(new InputStreamReader(connection.getInputStream()));
                String inputLine;
                StringBuffer response = new StringBuffer();

                while ((inputLine = in.readLine()) != null) {
                    response.append(inputLine);
                }
                in.close();

                // Print the response content (you can do whatever processing you want with it)
                System.out.println("Response Content:");

                // Print first 100 characters of the response
                System.out.println(response.substring(0, 100));

            } catch (IOException e) {
                System.out.println("Error while sending GET request: " + e.getMessage());
            }

            try {
                // Pause the loop for 3 seconds
                Thread.sleep(3000);
            } catch (InterruptedException e) {
                System.out.println("Thread interrupted: " + e.getMessage());
            }
        }
    }
}
