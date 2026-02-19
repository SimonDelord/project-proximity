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
 * 
 * Handles multiple payload formats:
 * 1. Direct format: { "identification": { "truck_id": "...", "firmware_version": "..." }, ... }
 * 2. Wrapped format: { "key": "...", "value": { "identification": { ... } } }
 * 3. Legacy format: { "data": { "identification": { ... } } }
 */
@ApplicationScoped
public class TruckEdaFilterRoute extends RouteBuilder {

    @ConfigProperty(name = "kafka.source.topic", defaultValue = "truck-telemetry-aap")
    String sourceTopic;

    @ConfigProperty(name = "kafka.target.topic", defaultValue = "truck-telemetry-aap-eda")
    String targetTopic;

    @ConfigProperty(name = "kafka.brokers", defaultValue = "my-cluster-kafka-bootstrap:9092")
    String kafkaBrokers;

    @ConfigProperty(name = "kafka.consumer.group", defaultValue = "truck-eda-filter-aap-group")
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
            .routeId("truck-eda-filter-aap-route")
            
            .log("============================================================")
            .log("Received message from " + sourceTopic)
            .log("Raw message: ${body}")
            
            // Unmarshal JSON to Map
            .unmarshal().json(JsonLibrary.Jackson, Map.class)
            
            // Extract and filter the data - handles multiple formats
            .process(exchange -> {
                @SuppressWarnings("unchecked")
                Map<String, Object> payload = exchange.getIn().getBody(Map.class);
                
                String truckId = "unknown";
                String firmwareVersion = "unknown";
                
                // Try to find the identification object in various payload structures
                Map<String, Object> identification = findIdentification(payload);
                
                if (identification != null) {
                    Object truckIdObj = identification.get("truck_id");
                    Object firmwareObj = identification.get("firmware_version");
                    
                    if (truckIdObj != null) {
                        truckId = truckIdObj.toString();
                    }
                    if (firmwareObj != null) {
                        firmwareVersion = firmwareObj.toString();
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
    
    /**
     * Finds the identification object in various payload structures:
     * 1. Direct: payload.identification
     * 2. Wrapped: payload.value.identification
     * 3. Legacy: payload.data.identification
     */
    @SuppressWarnings("unchecked")
    private Map<String, Object> findIdentification(Map<String, Object> payload) {
        if (payload == null) {
            return null;
        }
        
        // Format 1: Direct - { "identification": { ... } }
        if (payload.containsKey("identification")) {
            Object id = payload.get("identification");
            if (id instanceof Map) {
                return (Map<String, Object>) id;
            }
        }
        
        // Format 2: Wrapped - { "key": "...", "value": { "identification": { ... } } }
        if (payload.containsKey("value")) {
            Object value = payload.get("value");
            if (value instanceof Map) {
                Map<String, Object> valueMap = (Map<String, Object>) value;
                if (valueMap.containsKey("identification")) {
                    Object id = valueMap.get("identification");
                    if (id instanceof Map) {
                        return (Map<String, Object>) id;
                    }
                }
            }
        }
        
        // Format 3: Legacy - { "data": { "identification": { ... } } }
        if (payload.containsKey("data")) {
            Object data = payload.get("data");
            if (data instanceof Map) {
                Map<String, Object> dataMap = (Map<String, Object>) data;
                if (dataMap.containsKey("identification")) {
                    Object id = dataMap.get("identification");
                    if (id instanceof Map) {
                        return (Map<String, Object>) id;
                    }
                }
            }
        }
        
        return null;
    }
}

