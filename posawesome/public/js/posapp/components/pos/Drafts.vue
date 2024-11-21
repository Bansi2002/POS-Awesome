<template>
  <v-row justify="center">
    <v-dialog v-model="draftsDialog" max-width="900px">
      <v-card>
        <v-card-title>
          <span class="headline primary--text">{{ __('Select Hold Invoice') }}</span>
        </v-card-title>
        <v-card-text class="pa-0">
          <v-container>
            <v-row no-gutters>
              <v-col cols="12" class="pa-1">
                <v-data-table :headers="headers" :items="dialog_data" item-key="name" class="elevation-1"
                  :single-select="singleSelect" show-select v-model="selected">
                  <template v-slot:item.name="{ item }">
                    <v-row @click="viewInvoiceDetail(item)">
                      <v-col>{{ item.name }}</v-col>
                    </v-row>
                  </template>

                  <template v-slot:item.posting_time="{ item }">
                    {{ item.posting_time.split('.')[0] }}
                  </template>
                  <template v-slot:item.grand_total="{ item }">
                    {{ currencySymbol(item.currency) }} {{ formtCurrency(item.grand_total) }}
                  </template>
                </v-data-table>
              </v-col>
            </v-row>
          </v-container>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" dark @click="close_dialog">Close</v-btn>
          <v-btn color="success" dark @click="submit_dialog">Select</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="invoiceDetailDialog" max-width="700px">
      <v-card>
        <v-card-title>
          <span class="headline">{{ __('Invoice Item Details') }}</span>
        </v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12">
              <v-divider></v-divider>

              <v-data-table :headers="invoiceHeaders" :items="selectedInvoice" item-key="item_name" class="elevation-1"
                hide-default-footer>
                <template v-slot:item.rate="{ item }">
                  {{ currencySymbol(item.currency) }} {{ formtCurrency(item.rate) }}
                </template>
                <template v-slot:item.amount="{ item }">
                  {{ currencySymbol(item.currency) }} {{ formtCurrency(item.amount) }}
                </template>
              </v-data-table>
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" dark @click="closeDetailDialog">Close</v-btn>
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
    draftsDialog: false,
    invoiceDetailDialog: false,
    singleSelect: true,
    selected: [],
    dialog_data: [],
    selectedInvoice: [], 
    headers: [
      {
        text: __('Customer'),
        value: 'customer_name',
        align: 'start',
        sortable: true,
      },
      {
        text: __('Date'),
        align: 'start',
        sortable: true,
        value: 'posting_date',
      },
      {
        text: __('Time'),
        align: 'start',
        sortable: true,
        value: 'posting_time',
      },
      {
        text: __('Invoice'),
        value: 'name',
        align: 'start',
        sortable: true,
      },
      {
        text: __('Amount'),
        value: 'grand_total',
        align: 'end',
        sortable: false,
      },
    ],
    invoiceHeaders: [
      { text: 'Item Name', value: 'item_name', align: 'start' },
      { text: 'QTY', value: 'qty', align: 'start' },
      { text: 'UOM', value: 'uom', align: 'start' },
      { text: 'Rate', value: 'rate', align: 'start' },
      { text: 'Amount', value: 'amount', align: 'start' },

    ],
  }),
  methods: {
    close_dialog() {
      this.draftsDialog = false;
    },

    submit_dialog() {
      if (this.selected.length > 0) {
        evntBus.$emit('load_invoice', this.selected[0]);
        this.draftsDialog = false;
      }
    },

    viewInvoiceDetail(invoice_name) {
      frappe.call({
        method: "posawesome.posawesome.api.posapp.get_sales_invoice_child_table",
        args: {
          sales_invoice: invoice_name.name,
        },
        callback: (r) => {
          if (r.message) {
            this.selectedInvoice = r.message;  
            this.invoiceDetailDialog = true;  
          }
        },
      });
    },


    closeDetailDialog() {
      this.invoiceDetailDialog = false; 
    },
  },
  created() {
    evntBus.$on('open_drafts', (data) => {
      this.draftsDialog = true;
      this.dialog_data = data;
    });
  },
};
</script>