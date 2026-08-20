import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import { Construct } from 'constructs';

/**
 * Props parametrizadas de la pila: permiten reutilizar la misma definicion
 * de infraestructura para distintos entornos (dev, staging, prod) sin
 * duplicar codigo, tal como describe el post en "Patrones avanzados".
 */
export interface WebsiteStackProps extends cdk.StackProps {
  readonly environment: string;
}

/**
 * Pila que despliega un sitio estatico en S3 servido a traves de CloudFront.
 * Es el mismo ejemplo del post ("Definiendo recursos con construcciones de
 * alto nivel"), con dos ajustes para que corra en minutos sin cuenta AWS:
 *  - construccion moderna `cloudfront.Distribution` en vez de la legacy
 *    `CloudFrontWebDistribution` (ambas equivalentes a nivel conceptual)
 *  - acceso al bucket restringido vía OAC en lugar de publicReadAccess
 */
export class WebsiteStack extends cdk.Stack {
  public readonly bucket: s3.Bucket;
  public readonly distribution: cloudfront.Distribution;

  constructor(scope: Construct, id: string, props: WebsiteStackProps) {
    super(scope, id, props);

    const bucketName = `${props.environment}-website-devopsfreelance-demo`;

    this.bucket = new s3.Bucket(this, 'WebsiteBucket', {
      bucketName,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
    });

    this.distribution = new cloudfront.Distribution(this, 'Distribution', {
      defaultRootObject: 'index.html',
      defaultBehavior: {
        origin: new origins.S3Origin(this.bucket),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
      },
      comment: `Distribucion CDK - entorno ${props.environment}`,
    });

    new s3deploy.BucketDeployment(this, 'DeployWebsite', {
      sources: [s3deploy.Source.asset('./website-content')],
      destinationBucket: this.bucket,
      distribution: this.distribution,
      distributionPaths: ['/*'],
    });

    new cdk.CfnOutput(this, 'BucketNameOutput', { value: this.bucket.bucketName });
    new cdk.CfnOutput(this, 'DistributionDomainName', {
      value: this.distribution.distributionDomainName,
    });
  }
}
