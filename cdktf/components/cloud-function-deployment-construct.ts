import { Construct } from "constructs";

import { ArchiveProvider } from "../.gen/providers/archive/provider";
import { GoogleAppEngineApplication } from "../.gen/providers/google-beta/google-app-engine-application";
import { GoogleProjectService } from "../.gen/providers/google-beta/google-project-service";
import { GoogleStorageBucket } from "../.gen/providers/google-beta/google-storage-bucket";
import { RandomProvider } from "../.gen/providers/random/provider";
import { StringResource } from "../.gen/providers/random/string-resource";


export interface CloudFunctionDeploymentConstructProps {
    readonly project: string;
    readonly region: string;
    readonly randomProvider: RandomProvider;
    readonly archiveProvider: ArchiveProvider;
}

export class CloudFunctionDeploymentConstruct extends Construct{
    public readonly sourceBucket: GoogleStorageBucket;
    public readonly project: string;
    public readonly region: string;

    public readonly apis = [
        "iam.googleapis.com",
        "cloudresourcemanager.googleapis.com",
        "apikeys.googleapis.com",
        "run.googleapis.com",
        "artifactregistry.googleapis.com",
        "cloudfunctions.googleapis.com",
        "storage-api.googleapis.com",
        "storage-component.googleapis.com",
        "cloudbuild.googleapis.com",
        "eventarc.googleapis.com",
        "secretmanager.googleapis.com",
        "logging.googleapis.com",
    ];

    public readonly services: GoogleProjectService[];

    constructor(scope: Construct, id: string, props: CloudFunctionDeploymentConstructProps) {
        super(scope, id);


        this.project = props.project;
        this.region = props.region;

        this.services = [];
        for (const api of this.apis) {
            this.services.push(new GoogleProjectService(this, `${api.replaceAll(".", "")}`, {
                project: props.project,
                service: api,
                disableOnDestroy: false,
            }));
        }

        const bucketSuffix = new StringResource(this, "bucketPrefix", {
            length: 8,
            special: false,
            upper: false,
        })

        this.sourceBucket = new GoogleStorageBucket(this, "sourceBucket", {
            name: "source" + bucketSuffix.result,
            project: props.project,
            location: props.region,
            storageClass: "REGIONAL",
            forceDestroy: true,
            uniformBucketLevelAccess: true,
            lifecycleRule: [{
                action: {
                    type: "Delete"
                },
                condition: {
                    age: 1
                }
            }],
            dependsOn: this.services
        });

        // This is a hack to enable datastore API for the project
        // https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/datastore_index
        new GoogleAppEngineApplication(this, "app-engine-application", {
            locationId: props.region,
            project: props.project,
            databaseType: "CLOUD_DATASTORE_COMPATIBILITY",
            dependsOn: this.services
        });
    }
}