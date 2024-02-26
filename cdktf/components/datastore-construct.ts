
import { Construct } from "constructs";
import { GoogleProjectIamMember } from "../.gen/providers/google-beta/google-project-iam-member";
import { GoogleServiceAccount } from "../.gen/providers/google-beta/google-service-account";
import { GoogleProjectService } from "../.gen/providers/google-beta/google-project-service";

export interface DatastoreConstructProps {
    readonly project: string;
    readonly servicesAccount: GoogleServiceAccount;
}

export class DatastoreConstruct extends Construct {

    public readonly apis = [
        "datastore.googleapis.com",
    ];

    private constructor(scope: Construct, id: string, props: DatastoreConstructProps) {
        super(scope, id);
        const services = [];
        for (const api of this.apis) {
            services.push(new GoogleProjectService(this, `${api.replaceAll(".", "")}`, {
                project: props.project,
                service: api,
                disableOnDestroy: false,
            }));
        }
    }

    private async build(props: DatastoreConstructProps) {
        new GoogleProjectIamMember(this, "DatastoreProjectIamMember", {
            project: props.project,
            role: "roles/datastore.user",
            member: "serviceAccount:" + props.servicesAccount.email,
        });
    }

    public static async create(scope: Construct, id: string, props: DatastoreConstructProps) {
        const me = new DatastoreConstruct(scope, id, props);
        await me.build(props);
        return me;
    }
}