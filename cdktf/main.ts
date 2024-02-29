import { Construct } from "constructs";
import { App, TerraformOutput, TerraformStack } from "cdktf";
import { ArchiveProvider } from "./.gen/providers/archive/provider";
import { RandomProvider } from "./.gen/providers/random/provider";
import { DataGoogleBillingAccount } from "./.gen/providers/google-beta/data-google-billing-account";
import { GoogleDatastoreIndex } from "./.gen/providers/google-beta/google-datastore-index";


import { GoogleBetaProvider } from "./.gen/providers/google-beta/provider/index";
import { GoogleProject } from "./.gen/providers/google-beta/google-project";
import { CloudFunctionDeploymentConstruct } from "./components/cloud-function-deployment-construct";
import { CloudFunctionConstruct } from "./components/cloud-function-construct";

import * as dotenv from 'dotenv';
import { ApigatewayConstruct } from "./components/api-gateway-construct";
import { DatastoreConstruct } from "./components/datastore-construct";
import { GoogleProjectIamMember } from "./.gen/providers/google-beta/google-project-iam-member";
import { GoogleProjectService } from "./.gen/providers/google-beta/google-project-service";
dotenv.config();

class GeminiReaderRunnerStack extends TerraformStack {
  constructor(scope: Construct, id: string) {
    super(scope, id);

    // define resources here
  }
  async buildGcpLabEngineStack() {
    const projectId = process.env.PROJECTID!;

    const googleBetaProvider = new GoogleBetaProvider(this, "google", {
      region: process.env.REGION!,
    });
    const archiveProvider = new ArchiveProvider(this, "archive", {});
    const randomProvider = new RandomProvider(this, "random", {});

    const billingAccount = new DataGoogleBillingAccount(this, "billing-account", {
      billingAccount: process.env.BillING_ACCOUNT!,
    });

    const project = new GoogleProject(this, "project", {
      projectId: projectId,
      name: projectId,
      billingAccount: billingAccount.id,
      skipDelete: false
    });

    const cloudFunctionDeploymentConstruct =
      new CloudFunctionDeploymentConstruct(this, "cloud-function-deployment", {
        project: project.projectId,
        region: process.env.REGION!,
        archiveProvider: archiveProvider,
        randomProvider: randomProvider,
      });

    const translateService = new GoogleProjectService(this, `translateService`, {
      project: project.projectId,
      service: "translate.googleapis.com",
      disableOnDestroy: false,
    })
    cloudFunctionDeploymentConstruct.services.push(translateService);

    //For the first deployment, it takes a while for API to be enabled.
    await new Promise(r => setTimeout(r, 30000));

    const geminiImgDescCloudFunctionConstruct = await CloudFunctionConstruct.create(this, "geminiImgDescCloudFunctionConstruct", {
      functionName: "geminiimgdesc",
      runtime: "python311",
      entryPoint: "geminiimgdesc",
      timeout: 600,
      availableCpu: "1",
      availableMemory: "1Gi",
      makePublic: false,
      cloudFunctionDeploymentConstruct: cloudFunctionDeploymentConstruct,
      environmentVariables: {
        "MODEL_NAME": process.env.MODEL_NAME!,
        "DAILY_BUDGET": process.env.DAILY_BUDGET!,
        "LANGCHAIN_TRACING_V2": process.env.LANGCHAIN_TRACING_V2!,
        "LANGCHAIN_API_KEY": process.env.LANGCHAIN_API_KEY!,
      },
    });  

    await DatastoreConstruct.create(this, " geminiImgDescDatastore", {
      project: project.projectId,
      servicesAccount: geminiImgDescCloudFunctionConstruct.serviceAccount,
    });

    new GoogleDatastoreIndex(this, "google_datastore_index", {
      project: project.projectId,
      kind: "Usage",
      properties: [
        {
          name: "user_id",
          direction: "ASCENDING",
        },
        {
          name: "time",
          direction: "DESCENDING",
        },
        {
          name: "cost",
          direction: "DESCENDING",
        },
      ],
    });
    new GoogleDatastoreIndex(this, "google_datastore_index_2", {
      project: project.projectId,
      kind: "Usage",
      properties: [
        {
          name: "model_region",
          direction: "ASCENDING",
        },
        {
          name: "time",
          direction: "DESCENDING",
        }
      ],
    });

    new GoogleProjectIamMember(this, "AiplatformProjectIamMember", {
      project: project.id,
      role: "roles/aiplatform.user",
      member: "serviceAccount:" + geminiImgDescCloudFunctionConstruct.serviceAccount.email,
    });
    
    new GoogleProjectIamMember(this, "CloudtranslateProjectIamMember", {
      project: project.id,
      role: "roles/cloudtranslate.user",
      member: "serviceAccount:" + geminiImgDescCloudFunctionConstruct.serviceAccount.email,
    });

    const apigatewayConstruct = await ApigatewayConstruct.create(this, "api-gateway", {
      api: "geminiimagerunnerapi",
      project: project.projectId,
      provider: googleBetaProvider,
      replaces: { "GEMINI": geminiImgDescCloudFunctionConstruct.cloudFunction.url },
      servicesAccount: geminiImgDescCloudFunctionConstruct.serviceAccount,
    });

    new TerraformOutput(this, "project-id", {
      value: project.projectId,
    });

    new TerraformOutput(this, "api-url", {
      value: apigatewayConstruct.gateway.defaultHostname,
    });

    new TerraformOutput(this, "service-name", {
      value: apigatewayConstruct.apiGatewayApi.managedService,
    });

  }
}

async function buildStack(scope: Construct, id: string) {
  const stack = new GeminiReaderRunnerStack(scope, id);
  await stack.buildGcpLabEngineStack();
}

async function createApp(): Promise<App> {
  const app = new App();
  await buildStack(app, "cdktf");
  return app;
}

createApp().then((app) => app.synth());