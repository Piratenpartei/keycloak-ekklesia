import * as React from "react";
import { Form, FormGroup, TextInput, ActionGroup, Button, Checkbox, PageSection, PageSectionVariants } from "@patternfly/react-core";
import { ContentPage } from "../ContentPage";
import { ContentAlert } from "../ContentAlert";
import { Msg } from "../../widgets/Msg";
import { AccountServiceContext } from '../../account-service/AccountServiceContext';
import { HttpResponse } from '../../account-service/account.service';

interface BeoPageProps {}

interface FormFields {
  readonly username?: string;
  readonly firstName?: string;
  readonly lastName?: string;
  readonly email?: string;
  attributes?: { notify_matrix_ids?: string[], notify_enable_email?: string[] | boolean };
}

interface NotifySettings {
  formFields: FormFields
}

export class EkklesiaBeoSettings extends React.Component {
    static contextType = AccountServiceContext;
    context: React.ContextType<typeof AccountServiceContext>;

    private readonly DEFAULT_STATE: NotifySettings = {
      formFields: {},
    };
    public state: NotifySettings = this.DEFAULT_STATE;

    constructor(props: BeoPageProps, context: React.ContextType<typeof AccountServiceContext>) {
      super(props);
      this.context = context;
      this.fetchPersonalInfo();
    }

    fetchPersonalInfo() {
      this.context!.doGet<FormFields>("/")
        .then((response: HttpResponse<FormFields>) => {
          this.setState(this.DEFAULT_STATE);
          const formFields = response.data;
          if (!formFields!.attributes) {
              formFields!.attributes = { notify_matrix_ids: [] };
          }
          if (!formFields!.attributes.notify_matrix_ids) {
              formFields!.attributes.notify_matrix_ids = [];
          }
          let enable_email = formFields!.attributes.notify_enable_email;
          if (typeof enable_email !== "object" || enable_email.length != 1) {
            formFields!.attributes.notify_enable_email = true;
          } else {
            formFields!.attributes.notify_enable_email = enable_email[0] === "true";
          }

          this.setState({...{ formFields: formFields }});
        });
    }

    private handleChange = (value: string, event: React.FormEvent<HTMLInputElement>) => {
      let formFields = this.state.formFields;
      const target = event.currentTarget;
      const name = target.name;
      const matrix_ids = this.state.formFields.attributes!.notify_matrix_ids!;
      if (name === "beo-setting-matrix") {
        let elem = event.target as HTMLInputElement;
        let id = parseInt(elem.classList[elem.classList.length - 1]);
        matrix_ids[id] = value;
      }
      formFields.attributes!.notify_matrix_ids = matrix_ids;

      this.setState({...{ formFields: formFields }});
    }

    private handleCheckChange = (value: boolean, event: React.FormEvent<HTMLInputElement>) => {
      let formFields = this.state.formFields;
      const target = event.currentTarget;
      const id = target.id;
      formFields.attributes!.notify_enable_email = id === "beo-setting-enable-email" ? value : this.state.formFields.attributes!.notify_enable_email!;
      this.setState({...{ formFields: formFields }});
    }

    private handleCancel = (): void => {
      this.fetchPersonalInfo();
    }

    private handleSubmit = (event: React.FormEvent<HTMLFormElement>): void => {
      event.preventDefault();

      const reqData: FormFields = { ...this.state.formFields };
      const matrixIds = reqData.attributes!.notify_matrix_ids!;
      // Remove empty fields
      reqData.attributes!.notify_matrix_ids = matrixIds.filter(id => id);
      this.setState({...{ formFields: reqData }});

      this.context!.doPost<void>("/", reqData)
          .then(() => {
              ContentAlert.success('accountUpdatedMessage');
          })
          .catch(() => {
              ContentAlert.warning("accountUpdateFailedReload");
          });
    }

    private addMatrix = (): void => {
      let formFields = this.state.formFields;
      formFields.attributes!.notify_matrix_ids!.push("");
      this.setState({...{ formFields: formFields }});
    }

    render(): React.ReactNode {
      let matrix_ids : string[] = [];
      if (this.state.formFields.attributes && this.state.formFields.attributes.notify_matrix_ids) {
        matrix_ids = this.state.formFields.attributes!.notify_matrix_ids!;
      }
      let checked = true;
      if (this.state.formFields.attributes && typeof this.state.formFields.attributes.notify_enable_email === "boolean") {
        checked = this.state.formFields.attributes!.notify_enable_email;
      }
      return (
        <ContentPage title="ekklesia-beo-settings" introMessage="ekklesia-beo-intro">
         <PageSection isFilled variant={PageSectionVariants.light}>
          <Form className="ekklesia-beo-form" isHorizontal onSubmit={event => this.handleSubmit(event)}>
            <FormGroup
              label="Email: "
              fieldId="beo-setting-email"
            >
              <Checkbox id="beo-setting-enable-email" isChecked={checked} onChange={this.handleCheckChange} label={this.state.formFields.email!}/>
            </FormGroup>
            <FormGroup
              label="Matrix-IDs: "
              fieldId="beo-setting-matrix"
            >
              {matrix_ids.map((id,idx) =>
                <TextInput
                  type="text"
                  className={""+idx}
                  name="beo-setting-matrix"
                  id={"beo-setting-matrix-"+idx}
                  value={id}
                  onChange={this.handleChange}
                  placeholder="@username:homeserver.tld"
                >
                </TextInput>
              )}
              <Button
                id="add-matrix-btn"
                variant="primary"
                onClick={this.addMatrix}
              >
                <Msg msgKey="ekklesia-beo-add-matrix" />
              </Button>
            </FormGroup>
            <ActionGroup>
              <Button
                  type="submit"
                  id="save-btn"
                  variant="primary"
              >
                  <Msg msgKey="doSave" />
              </Button>
              <Button
                  id="cancel-btn"
                  variant="secondary"
                  onClick={this.handleCancel}
              >
                  <Msg msgKey="doCancel" />
              </Button>
            </ActionGroup>
          </Form>
          </PageSection>
        </ContentPage>
      );
    }
}
