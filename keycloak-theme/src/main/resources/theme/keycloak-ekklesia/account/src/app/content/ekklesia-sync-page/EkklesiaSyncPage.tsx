import * as React from 'react';

import {
    DataList, DataListItemRow, DataListCell, DataListItemCells, PageSection, PageSectionVariants, TextInput, FormGroup, Button, Form
} from '@patternfly/react-core';
import { ContentPage } from "../ContentPage";
import { Msg } from "../../widgets/Msg";
import { ContentAlert } from "../ContentAlert";
import { AccountServiceContext } from '../../account-service/AccountServiceContext';

interface SyncPageProps {}

interface SyncPageState {
    formFields: FormFields
}

interface FormFields {
    attributes: SyncInformation;
}

interface SyncInformation {
    ekklesia_first_sync: string | null;
    ekklesia_last_sync: string | null;
    ekklesia_eligible: string | null;
    ekklesia_verified: string | null;
    ekklesia_department: string | null;
    ekklesia_external_voting: string | null;
    ekklesia_disable_reason_display: string | null;
    ekklesia_sync_id: string | null;
    sync_id: string | null;
}

export class EkklesiaSyncPage extends React.Component {
    static contextType = AccountServiceContext;
    context: React.ContextType<typeof AccountServiceContext>;
    private readonly DEFAULT_ATTRIBUTES: SyncInformation = {
        ekklesia_first_sync: null,
        ekklesia_last_sync: null,
        ekklesia_eligible: null,
        ekklesia_verified: null,
        ekklesia_department: null,
        ekklesia_external_voting: null,
        ekklesia_disable_reason_display: null,
        ekklesia_sync_id: null,
        sync_id: null
    };
    private readonly DEFAULT_STATE: SyncPageState = {
        formFields: {
            attributes: this.DEFAULT_ATTRIBUTES
        }
    };
    public state: SyncPageState = this.DEFAULT_STATE;

    public constructor(props: SyncPageProps, context: React.ContextType<typeof AccountServiceContext>) {
        super(props);
        this.context = context;
        this.fetchPersonalInfo();
    }

    private fetchPersonalInfo(): void {
        this.context!.doGet("/").then((response: any) => {
            this.setState(this.DEFAULT_STATE);
            let formData = response.data as FormFields;
            if (!formData.attributes) {
                formData.attributes = this.DEFAULT_ATTRIBUTES;
            }
            this.setState({ ...{formFields: formData} });
        });
    }

    private handleChange = (value: string, event: React.FormEvent<HTMLInputElement>) => {
        let formFields = this.state.formFields;
        formFields.attributes!.sync_id = value;
        this.setState({...{ formFields: formFields }});
    }

    private handleSubmit = (event: React.FormEvent<HTMLFormElement>): void => {
        event.preventDefault();
  
        const reqData = { ...this.state.formFields };
        this.context!.doPost<void>("/", reqData)
            .then(() => {
                ContentAlert.success('accountUpdatedMessage');
            });
      }

    public render(): React.ReactNode {
        let vals = this.state.formFields.attributes!;

        let dateVal = Date.parse(vals.ekklesia_last_sync!);
        let options = {year: 'numeric', month: 'numeric', day: 'numeric', hour: 'numeric', minute: 'numeric'};
        let date = isNaN(dateVal) ? "-" : new Intl.DateTimeFormat("default", options).format(dateVal);

        let eligible = vals.ekklesia_eligible == "true" ? Msg.localize("ekklesia-yes") : Msg.localize("ekklesia-no");
        let verified = vals.ekklesia_verified == "true" ? Msg.localize("ekklesia-yes") : Msg.localize("ekklesia-no");
        let external_voting = vals.ekklesia_external_voting == "true" ? Msg.localize("ekklesia-yes") : Msg.localize("ekklesia-no");
        let department = vals.ekklesia_department ? vals.ekklesia_department : Msg.localize("ekklesia-unknown");
        let disable_reason = vals.ekklesia_disable_reason_display;
        let sync_id = vals.sync_id!;

        let sync_content;
        if (!vals.ekklesia_department) {
            if (disable_reason) {
                sync_content = <DataListItemRow>
                    <DataListItemCells dataListCells={[
                        <DataListCell width={4}>
                            <p><strong><Msg msgKey="ekklesia-disabled" /></strong> {disable_reason}</p>
                        </DataListCell>
                    ]}/>
                </DataListItemRow>;
            } else {
                sync_content = <DataListItemRow>
                    <DataListItemCells dataListCells={[
                        <DataListCell width={4}>
                            <p><strong><Msg msgKey="ekklesia-not-yet-synced" /></strong></p>
                        </DataListCell>
                    ]}/>
                </DataListItemRow>;
            }
        } else {
            sync_content = <div>
                <DataListItemRow>
                    <DataListItemCells dataListCells={[
                        <DataListCell width={1}>
                            <p><strong>
                                <Msg msgKey="ekklesia-sync-last" />
                            </strong></p>
                        </DataListCell>,
                        <DataListCell width={3}>
                            <p>{date}</p>
                        </DataListCell>
                    ]}/>
                </DataListItemRow>
                <DataListItemRow>
                    <DataListItemCells dataListCells={[
                        <DataListCell width={1}>
                            <p><strong>
                                <Msg msgKey="ekklesia-sync-eligible" />
                            </strong></p>
                        </DataListCell>,
                        <DataListCell width={3}>
                            <p>{eligible}</p>
                        </DataListCell>
                    ]}/>
                </DataListItemRow>
                <DataListItemRow>
                    <DataListItemCells dataListCells={[
                        <DataListCell width={1}>
                            <p><strong>
                                <Msg msgKey="ekklesia-sync-verified" />
                            </strong></p>
                        </DataListCell>,
                        <DataListCell width={3}>
                            <p>{verified}</p>
                        </DataListCell>
                    ]}/>
                </DataListItemRow>
                <DataListItemRow>
                    <DataListItemCells dataListCells={[
                        <DataListCell width={1}>
                            <p><strong>
                                <Msg msgKey="ekklesia-sync-department" />
                            </strong></p>
                        </DataListCell>,
                        <DataListCell width={3}>
                            <p>{department}</p>
                        </DataListCell>
                    ]}/>
                </DataListItemRow>
                </div>;
        }

        let sync_token_form;
        if (!vals.ekklesia_sync_id) {
            sync_token_form = 
              <Form className="ekklesia-sync-form" isHorizontal onSubmit={event => this.handleSubmit(event)} isWidthLimited maxWidth="500px">
                <Msg msgKey="ekklesia-no-sync-token" />
                <FormGroup
                    label="Piratenlogin Token: "
                    fieldId="sync-setting-token"
                >
                    <TextInput
                        type="text"
                        id="sync-setting-token"
                        name="sync-setting-token"
                        maxLength={19}
                        onChange={this.handleChange}
                        value={sync_id}
                    >
                    </TextInput>
                </FormGroup>
                <Button
                    type="submit"
                    id="save-btn"
                    variant="primary"
                >
                    <Msg msgKey="doSave" />
                </Button>
                <br />
              </Form>;
        }


        return (
            <ContentPage title="ekklesia-sync-state" introMessage="ekklesia-sync-intro">
              <PageSection isFilled variant={PageSectionVariants.light}>
                {sync_token_form}
                <DataList aria-label="Synchronisationsdaten">
                    {sync_content}
                </DataList>
              </PageSection>
            </ContentPage>
        );
    }
}
