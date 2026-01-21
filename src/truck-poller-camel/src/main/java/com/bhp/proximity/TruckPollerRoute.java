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

    @ConfigProperty(name = "kafka.topic", defaultValue = "truck-telemetry")
    String kafkaTopic;

    @Override
    public void configure() throws Exception {
        
        // Error handling
        onException(Exception.class)
            .maximumRedeliveries(3)
            .redeliveryDelay(1000)
            .log("ERROR: Failed to process truck telemetry: ${exception.message}")
            .handled(true);

        // Main route: Timer -> HTTP GET -> Transform -> Kafka
        from("timer:truckPoller?period=" + (pollIntervalSeconds * 1000))
            .routeId("truck-poller-route")
            .log("============================================================")
            .log("Polling Truck API: " + truckApiUrl)
            
            // Call the Truck API
            .toD("http:" + truckApiUrl.replace("https://", "").replace("http://", "") + "?httpMethod=GET&bridgeEndpoint=true" + 
                 (truckApiUrl.startsWith("https") ? "&sslContextParameters=#sslContextParameters" : ""))
            
            // Log the response
            .log("Received truck data: ${body}")
            
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
                
                // Extract truck_id for Kafka key (parse from JSON)
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
            .to("kafka:" + kafkaTopic)
            .log("Successfully published truck telemetry to Kafka")
            .log("============================================================");
    }
}

