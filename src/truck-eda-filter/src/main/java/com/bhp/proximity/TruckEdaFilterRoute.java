package com.bhp.proximity;

import org.apache.camel.builder.RouteBuilder;
import org.apache.camel.component.kafka.KafkaConstants;
import org.apache.camel.model.dataformat.JsonLibrary;
import org.eclipse.microprofile.config.inject.ConfigProperty;

import jakarta.enterprise.context.ApplicationScoped;
import java.time.Instant;
import java.util.Map;

/**
 * Camel route that consumes truck telemetry from Kafka,
 * filters to extract truck_id and firmware_version,
 * and publishes to the EDA topic.
 */
@ApplicationScoped
public class TruckEdaFilterRoute extends RouteBuilder {

    @ConfigProperty(name = "kafka.source.topic", defaultValue = "truck-telemetry-camel")
    String sourceTopic;

    @ConfigProperty(name = "kafka.target.topic", defaultValue = "eda-topic")
    String targetTopic;

    @ConfigProperty(name = "kafka.brokers", defaultValue = "172.30.68.114:9092")
    String kafkaBrokers;

    @ConfigProperty(name = "kafka.consumer.group", defaultValue = "truck-eda-filter-group")
    String consumerGroup;

    @Override
    public void configure() throws Exception {

        // Error handling
        onException(Exception.class)
            .maximumRedeliveries(3)
            .redeliveryDelay(2000)
            .log("ERROR: ${exception.message}")
            .handled(true);

        // Main route: Consume from Kafka -> Filter -> Publish to EDA topic
        from("kafka:" + sourceTopic + 
             "?brokers=" + kafkaBrokers + 
             "&groupId=" + consumerGroup +
             "&autoOffsetReset=earliest")
            .routeId("truck-eda-filter-route")
            
            .log("============================================================")
            .log("Received message from " + sourceTopic)
            
            // Unmarshal JSON to Map
            .unmarshal().json(JsonLibrary.Jackson, Map.class)
            
            // Extract and filter the data
            .process(exchange -> {
                @SuppressWarnings("unchecked")
                Map<String, Object> payload = exchange.getIn().getBody(Map.class);
                
                // Get the nested data
                @SuppressWarnings("unchecked")
                Map<String, Object> data = (Map<String, Object>) payload.get("data");
                
                String truckId = "unknown";
                String firmwareVersion = "unknown";
                
                if (data != null) {
                    @SuppressWarnings("unchecked")
                    Map<String, Object> identification = (Map<String, Object>) data.get("identification");
                    
                    if (identification != null) {
                        truckId = (String) identification.getOrDefault("truck_id", "unknown");
                        firmwareVersion = (String) identification.getOrDefault("firmware_version", "unknown");
                    }
                }
                
                // Create filtered EDA message
                String edaMessage = String.format(
                    "{\"event_type\":\"truck_telemetry_filtered\"," +
                    "\"timestamp\":\"%s\"," +
                    "\"source_topic\":\"%s\"," +
                    "\"truck_id\":\"%s\"," +
                    "\"firmware_version\":\"%s\"}",
                    Instant.now().toString(),
                    sourceTopic,
                    truckId,
                    firmwareVersion
                );
                
                exchange.getIn().setBody(edaMessage);
                exchange.getIn().setHeader(KafkaConstants.KEY, truckId);
                
                // Store for logging
                exchange.setProperty("truckId", truckId);
                exchange.setProperty("firmwareVersion", firmwareVersion);
            })
            
            .log("Filtered: truck_id=${exchangeProperty.truckId}, firmware_version=${exchangeProperty.firmwareVersion}")
            
            // Publish to EDA topic
            .to("kafka:" + targetTopic + "?brokers=" + kafkaBrokers)
            
            .log("Published to " + targetTopic)
            .log("============================================================");
    }
}

