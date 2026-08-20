package main

import (
	"fmt"
	"log"
	"net/http"
)

func handler(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintln(w, "OK - servicio de ejemplo para optimizacion de imagenes Docker")
}

func main() {
	http.HandleFunc("/", handler)
	log.Println("Servidor escuchando en :8080")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatal(err)
	}
}
