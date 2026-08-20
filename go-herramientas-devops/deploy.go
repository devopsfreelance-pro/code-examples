package main

import (
	"fmt"
	"os"

	"gopkg.in/yaml.v3"
)

// Manifest representa la configuracion minima de un despliegue.
type Manifest struct {
	App         string   `yaml:"app"`
	Environment string   `yaml:"environment"`
	Replicas    int      `yaml:"replicas"`
	Image       string   `yaml:"image"`
	Ports       []int    `yaml:"ports"`
	Tags        []string `yaml:"tags"`
}

var validEnvironments = map[string]bool{
	"staging":    true,
	"production": true,
}

// loadManifest lee y parsea el archivo YAML de despliegue.
func loadManifest(path string) (*Manifest, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("no se pudo leer el manifest: %w", err)
	}

	var m Manifest
	if err := yaml.Unmarshal(data, &m); err != nil {
		return nil, fmt.Errorf("manifest YAML invalido: %w", err)
	}

	return &m, nil
}

// validateManifest aplica las reglas minimas que debe cumplir un manifest.
func validateManifest(m *Manifest) error {
	if m.App == "" {
		return fmt.Errorf("el campo 'app' es obligatorio")
	}
	if m.Image == "" {
		return fmt.Errorf("el campo 'image' es obligatorio")
	}
	if m.Replicas < 1 {
		return fmt.Errorf("replicas debe ser >= 1, recibido %d", m.Replicas)
	}
	if len(m.Ports) == 0 {
		return fmt.Errorf("debe declarar al menos un puerto en 'ports'")
	}
	return nil
}

// deployApplication sigue el patron de manejo de errores explicito de Go:
// cada paso retorna un error envuelto con contexto (%w) para poder
// hacer unwrap y decidir la accion correcta en capas superiores.
func deployApplication(environment string, manifestPath string) error {
	if !validEnvironments[environment] {
		return fmt.Errorf("entorno invalido: %q (valores validos: staging, production)", environment)
	}

	manifest, err := loadManifest(manifestPath)
	if err != nil {
		return fmt.Errorf("error cargando manifest: %w", err)
	}

	if err := validateManifest(manifest); err != nil {
		return fmt.Errorf("manifest invalido: %w", err)
	}

	fmt.Printf("Desplegando %s en entorno: %s\n", manifest.App, environment)
	fmt.Printf("  imagen:   %s\n", manifest.Image)
	fmt.Printf("  replicas: %d\n", manifest.Replicas)
	fmt.Printf("  puertos:  %v\n", manifest.Ports)
	fmt.Println("Despliegue simulado completado con exito.")

	return nil
}
