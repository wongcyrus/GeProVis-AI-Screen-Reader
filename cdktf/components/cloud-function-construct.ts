import { Construct } from "constructs";
import { hashElement } from 'folder-hash';
import { DataArchiveFile } from "../.gen/providers/archive/data-archive-file";
import { GoogleCloudRunServiceIamBinding } from "../.gen/providers/google-beta/google-cloud-run-service-iam-binding";
import { GoogleCloudfunctions2Function, GoogleCloudfunctions2FunctionEventTrigger } from "../.gen/providers/google-beta/google-cloudfunctions2-function";
import { GoogleCloudfunctions2FunctionIamBinding } from "../.gen/providers/google-beta/google-cloudfunctions2-function-iam-binding";
import { GoogleServiceAccount } from "../.gen/providers/google-beta/google-service-account";
import { GoogleStorageBucketObject } from "../.gen/providers/google-beta/google-storage-bucket-object";
import { CloudFunctionDeploymentConstruct } from "./cloud-function-deployment-construct";
import path = require("path");

export interface CloudFunctionConstructProps {
    readonly functionName: string;
    readonly functionCode?: string;
    readonly runtime: string;
    readonly entryPoint: string;
    readonly availableCpu?: string;
    readonly availableMemory?: string;
    readonly timeout?: number;
    readonly cloudFunctionDeploymentConstruct: CloudFunctionDeploymentConstruct;
    readonly environmentVariables?: { [key: string]: string };
    readonly eventTrigger?: GoogleCloudfunctions2FunctionEventTrigger;
    readonly makePublic?: boolean;
    readonly serviceAccount?: GoogleServiceAccount;
}

export class CloudFunctionConstruct extends Construct {
    public cloudFunction!: GoogleCloudfunctions2Function;
    public serviceAccount: GoogleServiceAccount;
    private props: CloudFunctionConstructProps;
    public project: string;

    private constructor(scope: Construct, id: string, props: CloudFunctionConstructProps) {
        super(scope, id);
        let accountId = props.functionName + props.entryPoint.replace(/[^a-z0-9]/gi, '');
        accountId = accountId.substring(0, 27).toLowerCase();

        if (props.serviceAccount) {
            this.serviceAccount = props.serviceAccount;
        } else {
            this.serviceAccount = new GoogleServiceAccount(this, "service-account", {
                accountId: accountId,
                project: props.cloudFunctionDeploymentConstruct.project,
                displayName: props.functionName + props.entryPoint ?? "",
            });
        }
        this.props = props;
        this.project = props.cloudFunctionDeploymentConstruct.project;
    }

    private async build(props: CloudFunctionConstructProps) {

        const options = {
            folders: { exclude: ['.*', "bin", "obj"] },
            files: { include: ['*.py', '*.txt', '*.zip'] },
        };
        const hash = await hashElement(path.resolve(__dirname, "..", "..", "functions", this.props.functionCode ?? this.props.functionName), options);
        const outputFileName = `function-source-${hash.hash}.zip`;
        const code = new DataArchiveFile(this, "archiveFile", {
            type: "zip",
            sourceDir: path.resolve(__dirname, "..", "..", "functions", this.props.functionCode ?? this.props.functionName),
            outputPath: path.resolve(__dirname, "..", "cdktf.out", "functions", outputFileName)
        });

        const storageBucketObject = new GoogleStorageBucketObject(this, "storage-bucket-object", {
            name: outputFileName,
            bucket: this.props.cloudFunctionDeploymentConstruct.sourceBucket.name,
            source: code.outputPath,
        });


        this.cloudFunction = new GoogleCloudfunctions2Function(this, "cloud-function", {
            name: this.props.functionName.toLowerCase(),
            project: this.props.cloudFunctionDeploymentConstruct.project,
            location: this.props.cloudFunctionDeploymentConstruct.region,
            buildConfig: {
                runtime: props.runtime,
                entryPoint: this.props.entryPoint ?? this.props.functionName,
                source: {
                    storageSource: {
                        bucket: this.props.cloudFunctionDeploymentConstruct.sourceBucket.name,
                        object: storageBucketObject.name,
                    }
                }
            },
            serviceConfig: {
                maxInstanceRequestConcurrency: 1,
                maxInstanceCount: 100,
                minInstanceCount: 0,
                availableCpu: props.availableCpu ?? "1",
                availableMemory: props.availableMemory ?? "128Mi",
                timeoutSeconds: props.timeout ?? 60,
                serviceAccountEmail: this.serviceAccount.email,
                environmentVariables: props.environmentVariables ?? {},
            },
            eventTrigger: props.eventTrigger,
            dependsOn: props.cloudFunctionDeploymentConstruct.services
        });

        const member = props.makePublic ?? false ? "allUsers" : "serviceAccount:" + this.serviceAccount.email;
        new GoogleCloudfunctions2FunctionIamBinding(this, "cloudfunctions2-function-iam-member", {
            project: this.cloudFunction.project,
            location: this.cloudFunction.location,
            cloudFunction: this.cloudFunction.name,
            role: "roles/cloudfunctions.invoker",
            members: [member]
        });

        new GoogleCloudRunServiceIamBinding(this, "cloud-run-service-iam-binding", {
            project: this.props.cloudFunctionDeploymentConstruct.project,
            location: this.cloudFunction.location,
            service: this.cloudFunction.name,
            role: "roles/run.invoker",
            members: [member]
        });
    }

    public static async create(scope: Construct, id: string, props: CloudFunctionConstructProps) {
        const me = new CloudFunctionConstruct(scope, id, props);
        await me.build(props);
        return me;
    }
}