package com.bhp.proximity;

import org.apache.camel.builder.RouteBuilder;
import org.apache.camel.component.kafka.KafkaConstants;
import org.eclipse.microprofile.config.inject.ConfigProperty;

import jakarta.enterprise.context.ApplicationScoped;
import java.time.Instant;

/**
 * Camel route that polls the Truck API and publishes telemetry data to Kafka.
 */
@ApplicationScoped
public class TruckPollerRoute extends RouteBuilder {

    @ConfigProperty(name = "truck.api.url", defaultValue = "https://project-proximity-git-trucks.apps.rosa.rosa-7zgvg.a9ec.p3.openshiftapps.com/trucks/sample")
    String truckApiUrl;

    @ConfigProperty(name = "poll.interval.seconds", defaultValue = "10")
    int pollIntervalSeconds;

    @ConfigProperty(name = "kafka.topic", defaultValue = "truck-telemetry-camel")
    String kafkaTopic;

    @ConfigProperty(name = "kafka.brokers", defaultValue = "172.30.68.114:9092")
    String kafkaBrokers;

    @Override
    public void configure() throws Exception {
        
        // Error handling
        onException(Exception.class)
            .maximumRedeliveries(3)
            .redeliveryDelay(2000)
            .log("ERROR: ${exception.message}")
            .handled(true);

        // Main route: Timer -> HTTP GET -> Transform -> Kafka
        from("timer:truckPoller?period=" + (pollIntervalSeconds * 1000))
            .routeId("truck-poller-route")
            .log("============================================================")
            .log("Polling Truck API: " + truckApiUrl)
            
            // Call the Truck API using https4 component (handles HTTPS)
            .toD(truckApiUrl + "?bridgeEndpoint=true")
            
            // Log the response
            .log("Received truck data successfully")
            
            // Transform the payload to add metadata
            .process(exchange -> {
                String originalBody = exchange.getIn().getBody(String.class);
                String timestamp = Instant.now().toString();
                
                // Wrap the truck data with metadata
                String wrappedPayload = String.format(
                    "{\"source\":\"truck-poller-camel\",\"polled_at\":\"%s\",\"api_url\":\"%s\",\"data\":%s}",
                    timestamp, truckApiUrl, originalBody
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
            .log("Publishing to Kafka topic: " + kafkaTopic)
            .toD("kafka:" + kafkaTopic + "?brokers=" + kafkaBrokers)
            .log("Successfully published truck telemetry to Kafka")
            .log("============================================================");
    }
}
