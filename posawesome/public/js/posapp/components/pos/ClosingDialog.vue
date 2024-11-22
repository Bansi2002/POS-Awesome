<template>
  <v-row justify="center">
    <v-dialog v-model="closingDialog" max-width="900px">
      <v-card>
        <v-card-title>
          <span class="headline primary--text">{{
            __('Closing POS Shift')
          }}</span>
        </v-card-title>
        <v-card-text class="pa-0">
          <v-container>
            <v-row>
              <v-col cols="12" class="pa-1">
                <template>
                  <v-data-table :headers="headers" :items="dialog_data.payment_reconciliation"
                    item-key="mode_of_payment" class="elevation-1" :items-per-page="itemsPerPage" hide-default-footer>
                    <template v-slot:item.closing_amount="props">
                      <v-edit-dialog :return-value.sync="props.item.closing_amount">
                        {{ currencySymbol(pos_profile.currency) }}
                        {{ formtCurrency(props.item.closing_amount) }}
                        <template v-slot:input>
                          <v-text-field v-model="props.item.closing_amount" :rules="[max25chars]"
                            :label="frappe._('Edit')" single-line counter type="number"></v-text-field>
                        </template>
                      </v-edit-dialog>
                    </template>

                    <template v-slot:item.difference="{ item }">
                      {{ currencySymbol(pos_profile.currency) }}
                      {{
                        formtCurrency(item.difference = item.closing_amount - item.expected_amount)
                      }}

                    </template>

                    <template v-slot:item.shift_status="{ item }">
                      <span :class="{
                        'text-success': item.difference > 0,
                        'text-info': item.difference === 0,
                        'text-danger': item.difference < 0
                      }">
                        {{ item.difference < 0 ? __('Shortage') : item.difference > 0 ? __('Overage') : __('') }}
                      </span>
                    </template>

                    <template v-slot:item.opening_amount="{ item }">
                      {{ currencySymbol(pos_profile.currency) }}
                      {{ formtCurrency(item.opening_amount) }}</template>
                    <template v-slot:item.expected_amount="{ item }">
                      {{ currencySymbol(pos_profile.currency) }}
                      {{ formtCurrency(item.expected_amount) }}</template>
                    <template v-slot:item.total_sales="{ item }">
                      {{ currencySymbol(pos_profile.currency) }}
                      {{ formtCurrency(item.total_sales = item.expected_amount - item.opening_amount) }}</template>
                  </v-data-table>
                </template>
              </v-col>
            </v-row>

          </v-container>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" dark @click="close_dialog">{{
            __('Close')
          }}</v-btn>
          <v-btn color="success" dark @click="submit_dialog">{{
            __('Submit')
          }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-row>
</template>

<script>
import { evntBus } from '../../bus';
import format from '../../format';
export default {
  mixins: [format],
  data: () => ({
    closingDialog: false,
    itemsPerPage: 20,
    dialog_data: {},
    pos_profile: '',
    headers: [
      {
        text: __('Mode of Payment'),
        value: 'mode_of_payment',
        align: 'start',
        sortable: true,
      },
      {
        text: __('Opening Amount'),
        align: 'end',
        sortable: true,
        value: 'opening_amount',
      },
      {
        text: __('Total Sales'),
        value: 'total_sales',
        align: 'end',
        sortable: true,
      },
      {
        text: __('Closing Amount'),
        value: 'closing_amount',
        align: 'end',
        sortable: true,
      },
    ],
    max25chars: (v) => v.length <= 20 || 'Input too long!', // TODO : should validate as number
    pagination: {},
  }),
  watch: {},

  methods: {
    close_dialog() {
      this.closingDialog = false;
    },
    submit_dialog() {
      this.dialog_data.payment_reconciliation.forEach(item => {

        item.shift_status = item.difference < 0 ? __('Shortage') : item.difference > 0 ? __('Overage') : __('');
      });

      evntBus.$emit('submit_closing_pos', this.dialog_data);
      this.closingDialog = false;
    },
  },

  created: function () {
    evntBus.$on('open_ClosingDialog', (data) => {
      this.closingDialog = true;
      this.dialog_data = data;
    });

    evntBus.$on('register_pos_profile', (data) => {
      this.pos_profile = data.pos_profile;

      if (!this.pos_profile.hide_expected_amount) {
        const hasExpectedAmount = this.headers.some(header => header.value === 'expected_amount');
        const hasDifference = this.headers.some(header => header.value === 'difference');
        const hasShiftStatus = this.headers.some(header => header.value === 'shift_status');

        if (!hasExpectedAmount) {
          this.headers.push({
            text: __('Expected Amount'),
            value: 'expected_amount',
            align: 'end',
            sortable: false,
          });
        }

        if (!hasDifference) {
          this.headers.push({
            text: __('Difference'),
            value: 'difference',
            align: 'end',
            sortable: false,
          });
        }
        if (!hasShiftStatus) {
          this.headers.push({
            text: __('Shift Status'),
            value: 'shift_status',
            align: 'end',
            sortable: false,
          });
        }
      }
    });
  },
};
</script>
