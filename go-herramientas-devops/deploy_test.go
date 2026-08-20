package main

import (
	"os"
	"testing"
)

func writeTempManifest(t *testing.T, content string) string {
	t.Helper()
	f, err := os.CreateTemp(t.TempDir(), "manifest-*.yaml")
	if err != nil {
		t.Fatalf("no se pudo crear manifest temporal: %v", err)
	}
	if _, err := f.WriteString(content); err != nil {
		t.Fatalf("no se pudo escribir manifest temporal: %v", err)
	}
	f.Close()
	return f.Name()
}

func TestDeployApplication(t *testing.T) {
	validManifest := `
app: checkout-service
environment: staging
replicas: 3
image: registry.example.com/checkout-service:1.4.0
ports: [8080]
tags: [go, devops]
`
	invalidManifest := `
app: ""
image: ""
replicas: 0
`

	validPath := writeTempManifest(t, validManifest)
	invalidPath := writeTempManifest(t, invalidManifest)

	tests := []struct {
		name         string
		environment  string
		manifestPath string
		wantErr      bool
	}{
		{"deploy staging con manifest valido", "staging", validPath, false},
		{"deploy production con manifest valido", "production", validPath, false},
		{"entorno invalido", "invalid-env", validPath, true},
		{"manifest invalido", "staging", invalidPath, true},
		{"manifest inexistente", "staging", "no-existe.yaml", true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := deployApplication(tt.environment, tt.manifestPath)
			if (err != nil) != tt.wantErr {
				t.Errorf("deployApplication(%q, %q) error = %v, wantErr %v",
					tt.environment, tt.manifestPath, err, tt.wantErr)
			}
		})
	}
}

func TestValidateManifest(t *testing.T) {
	tests := []struct {
		name    string
		m       Manifest
		wantErr bool
	}{
		{"manifest completo", Manifest{App: "svc", Image: "img:1", Replicas: 1, Ports: []int{80}}, false},
		{"sin app", Manifest{Image: "img:1", Replicas: 1, Ports: []int{80}}, true},
		{"sin image", Manifest{App: "svc", Replicas: 1, Ports: []int{80}}, true},
		{"replicas invalidas", Manifest{App: "svc", Image: "img:1", Replicas: 0, Ports: []int{80}}, true},
		{"sin puertos", Manifest{App: "svc", Image: "img:1", Replicas: 1}, true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := validateManifest(&tt.m)
			if (err != nil) != tt.wantErr {
				t.Errorf("validateManifest(%+v) error = %v, wantErr %v", tt.m, err, tt.wantErr)
			}
		})
	}
}
