package com.bhp.proximity;

import org.apache.camel.builder.RouteBuilder;
import org.apache.camel.component.kafka.KafkaConstants;
import org.eclipse.microprofile.config.inject.ConfigProperty;

import jakarta.enterprise.context.ApplicationScoped;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;

/**
 * Camel route that polls multiple Truck API endpoints and publishes telemetry data to Kafka.
 * Supports polling multiple trucks simultaneously.
 */
@ApplicationScoped
public class TruckPollerRoute extends RouteBuilder {

    @ConfigProperty(name = "truck.api.urls", defaultValue = "https://project-proximity-git-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample")
    String truckApiUrls;  // Comma-separated list of URLs

    @ConfigProperty(name = "poll.interval.seconds", defaultValue = "5")
    int pollIntervalSeconds;

    @ConfigProperty(name = "kafka.topic", defaultValue = "truck-telemetry-camel")
    String kafkaTopic;

    @ConfigProperty(name = "kafka.brokers", defaultValue = "172.30.68.114:9092")
    String kafkaBrokers;

    @Override
    public void configure() throws Exception {
        
        // Parse the comma-separated URLs
        List<String> urls = Arrays.asList(truckApiUrls.split(","));
        
        log.info("============================================================");
        log.info("Configuring Truck Poller for {} endpoints", urls.size());
        log.info("Poll interval: {} seconds", pollIntervalSeconds);
        log.info("Kafka topic: {}", kafkaTopic);
        log.info("============================================================");

        // Error handling
        onException(Exception.class)
            .maximumRedeliveries(3)
            .redeliveryDelay(2000)
            .log("ERROR polling truck: ${exception.message}")
            .handled(true);

        // Create a route for each truck endpoint
        for (int i = 0; i < urls.size(); i++) {
            String url = urls.get(i).trim();
            String routeId = "truck-poller-route-" + (i + 1);
            int truckNumber = i + 1;
            
            log.info("Creating route {} for URL: {}", routeId, url);

            from("timer:truckPoller" + truckNumber + "?period=" + (pollIntervalSeconds * 1000) + "&delay=" + (i * 500))
                .routeId(routeId)
                .log("Polling Truck " + truckNumber + ": " + url)
                
                // Call the Truck API
                .toD(url + "?bridgeEndpoint=true")
                
                // Transform the payload to add metadata
                .process(exchange -> {
                    String originalBody = exchange.getIn().getBody(String.class);
                    String timestamp = Instant.now().toString();
                    
                    // Wrap the truck data with metadata
                    String wrappedPayload = String.format(
                        "{\"source\":\"truck-poller-camel\",\"polled_at\":\"%s\",\"api_url\":\"%s\",\"truck_number\":%d,\"data\":%s}",
                        timestamp, url, truckNumber, originalBody
                    );
                    
                    exchange.getIn().setBody(wrappedPayload);
                    
                    // Extract truck_id for Kafka key
                    if (originalBody.contains("\"truck_id\"")) {
                        int start = originalBody.indexOf("\"truck_id\":\"") + 12;
                        int end = originalBody.indexOf("\"", start);
                        if (start > 11 && end > start) {
                            String truckId = originalBody.substring(start, end);
                            exchange.getIn().setHeader(KafkaConstants.KEY, truckId);
                        }
                    }
                })
                
                // Send to Kafka
                .to("kafka:" + kafkaTopic + "?brokers=" + kafkaBrokers)
                .log("Published Truck " + truckNumber + " to " + kafkaTopic);
        }
    }
}
