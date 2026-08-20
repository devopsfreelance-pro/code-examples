package main

import (
	"fmt"
	"math/rand"
	"sync"
	"time"
)

// hostResult guarda el resultado de consultar un host.
type hostResult struct {
	host    string
	healthy bool
	latency time.Duration
}

// checkHost simula una consulta de red (por ejemplo, un healthcheck HTTP).
func checkHost(host string) hostResult {
	// Simula latencia de red variable entre 50 y 300ms.
	delay := time.Duration(50+rand.Intn(250)) * time.Millisecond
	time.Sleep(delay)

	return hostResult{
		host:    host,
		healthy: true,
		latency: delay,
	}
}

// checkStatus consulta todos los hosts en paralelo usando goroutines,
// tal como lo haria una herramienta DevOps real al chequear multiples
// servidores sin bloquear la ejecucion secuencialmente.
func checkStatus(hosts []string) {
	var wg sync.WaitGroup
	results := make(chan hostResult, len(hosts))

	start := time.Now()

	for _, host := range hosts {
		wg.Add(1)
		go func(h string) {
			defer wg.Done()
			results <- checkHost(h)
		}(host)
	}

	go func() {
		wg.Wait()
		close(results)
	}()

	fmt.Printf("Consultando %d hosts en paralelo...\n\n", len(hosts))
	for r := range results {
		status := "OK"
		if !r.healthy {
			status = "FAIL"
		}
		fmt.Printf("  %-10s %-4s latencia=%v\n", r.host, status, r.latency)
	}

	fmt.Printf("\nTiempo total: %v (secuencial hubiera tardado la suma de cada latencia)\n", time.Since(start))
}
