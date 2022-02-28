import * as React from 'react';

import {
    DataList, DataListItemRow, DataListCell, DataListItemCells, Title
} from '@patternfly/react-core';
import { ContentPage } from "../ContentPage";
import { Msg } from "../../widgets/Msg";
import { AccountServiceContext } from '../../account-service/AccountServiceContext';

interface SyncPageProps {}

interface SyncGet {
    attributes: SyncInformation;
}

interface SyncState {
    syncValues: SyncInformation;
}

interface SyncInformation {
    ekklesia_first_sync: string | null;
    ekklesia_last_sync: string | null;
    ekklesia_eligible: string | null;
    ekklesia_verified: string | null;
    ekklesia_department: string | null;
}

export class EkklesiaSyncPage extends React.Component {
    static contextType = AccountServiceContext;
    context: React.ContextType<typeof AccountServiceContext>;
    private readonly DEFAULT_STATE: SyncState = {
        syncValues: {
            ekklesia_first_sync: null,
            ekklesia_last_sync: null,
            ekklesia_eligible: null,
            ekklesia_verified: null,
            ekklesia_department: null,
        }
    };
    public state: SyncState = this.DEFAULT_STATE;

    public constructor(props: SyncPageProps, context: React.ContextType<typeof AccountServiceContext>) {
        super(props);
        this.context = context;
        this.fetchPersonalInfo();
    }

    private fetchPersonalInfo(): void {
        this.context!.doGet("/").then((response: any) => {
            this.setState(this.DEFAULT_STATE);
            const syncValues = response.data.attributes;

            this.setState({ ...{
                    syncValues: syncValues as SyncInformation
                }
            });
        });
    }

    public render(): React.ReactNode {
        let vals = this.state.syncValues;

        let dateVal = Date.parse(vals.ekklesia_last_sync!);
        let options = {year: 'numeric', month: 'numeric', day: 'numeric', hour: 'numeric', minute: 'numeric'};
        let date = isNaN(dateVal) ? "-" : new Intl.DateTimeFormat("default", options).format(dateVal);

        let eligible = vals.ekklesia_eligible == "true" ? Msg.localize("ekklesia-yes") : Msg.localize("ekklesia-no");
        let verified = vals.ekklesia_verified == "true" ? Msg.localize("ekklesia-yes") : Msg.localize("ekklesia-no");

        let department = vals.ekklesia_department ? vals.ekklesia_department : Msg.localize("ekklesia-unknown");

        return (
            <ContentPage title="ekklesia-sync-state" introMessage="ekklesia-sync-intro">
                <DataList aria-label="idk">
                    <DataListItemRow>
                        <DataListItemCells dataListCells={[
                            <DataListCell width={4}>
                                <div className="pf-c-content"><Title headingLevel="h2" size="2xl"><Msg msgKey="ekklesia-sync-title" /></Title></div>
                            </DataListCell>
                        ]}/>
                    </DataListItemRow>
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
                </DataList>
            </ContentPage>
        );
    }
}
