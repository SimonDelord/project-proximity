package com.bhp.proximity;

import org.apache.camel.support.jsse.SSLContextParameters;
import org.apache.camel.support.jsse.TrustManagersParameters;

import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.inject.Produces;
import jakarta.inject.Named;

/**
 * SSL Configuration for HTTPS connections.
 */
@ApplicationScoped
public class SslConfig {

    @Produces
    @Named("sslContextParameters")
    public SSLContextParameters sslContextParameters() {
        TrustManagersParameters trustManagersParameters = new TrustManagersParameters();
        // Trust all certificates (for development/testing)
        // In production, configure proper trust store
        
        SSLContextParameters sslContextParameters = new SSLContextParameters();
        sslContextParameters.setTrustManagers(trustManagersParameters);
        
        return sslContextParameters;
    }
}

