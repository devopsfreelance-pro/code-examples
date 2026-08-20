# AWS CDK: Infraestructura como Código con TypeScript

Ejemplo de código para el post [AWS CDK: Infraestructura como Código con TypeScript](https://www.devopsfreelance.pro/blog/posts/aws-cdk-infraestructura/).

## Qué demuestra

El ejemplo central del post ("Definiendo recursos con construcciones de alto
nivel"): una pila de AWS CDK en TypeScript que define un sitio estático en S3
servido a través de CloudFront, usando construcciones L2 (`Bucket`,
`Distribution`, `BucketDeployment`) en vez de plantillas CloudFormation
escritas a mano. También incluye el patrón de "Patrones avanzados y mejores
prácticas": una pila parametrizada (`WebsiteStackProps`) que acepta el
entorno (`dev`, `staging`, `prod`) como argumento, en lugar de duplicar la
definición de infraestructura por entorno.

No hace falta cuenta de AWS ni desplegar nada real: el ejemplo usa
`cdk synth`, el comando que compila el código TypeScript a una plantilla
CloudFormation completa (el corazón conceptual del post) sin tocar
credenciales ni recursos en la nube.

Archivos:
- `bin/app.ts`: punto de entrada de la app CDK. Lee el contexto `environment`
  (default `dev`) e instancia la pila.
- `lib/website-stack.ts`: la pila `WebsiteStack`, parametrizada por entorno,
  con el bucket S3, la distribución CloudFront y el despliegue de contenido.
- `website-content/index.html`: archivo de ejemplo que `BucketDeployment`
  sube al bucket.
- `cdk.json`, `tsconfig.json`, `package.json`: configuración estándar de un
  proyecto `cdk init app --language typescript`.

## Requisitos

- Node.js 18+ y npm
- Nada más. No se necesita Docker, LocalStack ni credenciales de AWS: `cdk synth`
  solo compila y sintetiza la plantilla, no despliega.

## Pasos para correrlo

```bash
cd aws-cdk-infraestructura

# 1. Instalar dependencias (aws-cdk-lib, el CLI de CDK y TypeScript)
npm install

# 2. Sintetizar la plantilla CloudFormation para el entorno "dev" (default)
npx cdk synth

# 3. (Opcional) sintetizar para otro entorno usando la pila parametrizada
npx cdk synth -c environment=prod
```

El comando `cdk synth` compila `bin/app.ts` y `lib/website-stack.ts`, valida
tipos y propiedades (los errores de tipado que menciona el post aparecen acá,
antes de cualquier despliegue) y genera la plantilla en
`cdk.out/WebsiteStack-dev.template.json`.

Para ver la plantilla generada:

```bash
cat cdk.out/WebsiteStack-dev.template.json | head -60
```

## Salida esperada

`npx cdk synth` imprime en pantalla la plantilla CloudFormation completa
(recursos `AWS::S3::Bucket`, `AWS::CloudFront::Distribution`, el custom
resource de `BucketDeployment`, etc.) y termina con la sección de
`Outputs` con el nombre del bucket y el dominio de la distribución:

```
Outputs:
  BucketNameOutput:
    Value:
      Ref: WebsiteBucket75C24D94
  DistributionDomainName:
    Value:
      Fn::GetAtt:
        - Distribution830FAC52
        - DomainName
...
```

Con `-c environment=prod`, la pila generada se llama `WebsiteStack-prod` y el
nombre del bucket cambia a `prod-website-devopsfreelance-demo`: la misma
definición de infraestructura, reutilizada por entorno, sin copiar y pegar
código, tal como describe el post.

Si quisieras desplegar esto de verdad a una cuenta de AWS propia, el
siguiente paso sería `cdk bootstrap` (una única vez por cuenta/región) y
`npx cdk deploy` — pasos que este ejemplo no ejecuta a propósito para no
requerir credenciales ni generar costos.
