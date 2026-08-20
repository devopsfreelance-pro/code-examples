package main

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "devtool",
	Short: "Herramienta DevOps para gestion de infraestructura",
	Long:  `Un CLI de ejemplo en Go que ilustra el patron de las herramientas DevOps modernas: binario unico, subcomandos con Cobra y concurrencia con goroutines.`,
}

var deployCmd = &cobra.Command{
	Use:   "deploy",
	Short: "Valida y despliega un manifest en el entorno indicado",
	RunE: func(cmd *cobra.Command, args []string) error {
		environment, _ := cmd.Flags().GetString("env")
		manifestPath, _ := cmd.Flags().GetString("manifest")
		return deployApplication(environment, manifestPath)
	},
}

var statusCmd = &cobra.Command{
	Use:   "status",
	Short: "Consulta el estado de varios servidores en paralelo usando goroutines",
	RunE: func(cmd *cobra.Command, args []string) error {
		hosts, _ := cmd.Flags().GetStringSlice("hosts")
		checkStatus(hosts)
		return nil
	},
}

func init() {
	deployCmd.Flags().StringP("env", "e", "staging", "Entorno de despliegue (staging|production)")
	deployCmd.Flags().StringP("manifest", "m", "manifest.yaml", "Ruta al manifest a validar")

	statusCmd.Flags().StringSlice("hosts", []string{"web-01", "web-02", "web-03"}, "Lista de hosts a consultar")

	rootCmd.AddCommand(deployCmd)
	rootCmd.AddCommand(statusCmd)
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
