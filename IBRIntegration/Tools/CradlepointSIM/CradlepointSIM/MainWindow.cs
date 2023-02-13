using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using CradlepointSIM.MQTTClient;

namespace CradlepointSIM
{
   public partial class MainWindow : Form
   {

      MainMQTTClient _mQTTClient = new MainMQTTClient();

      public MainWindow()
      {
         InitializeComponent();

         model_cxbx.SelectedIndex = 0;
         con_hidden_control_tbl.Visible = false; // hide connection rdo btns

      }

      delegate void connectionDelegate(object sender, EventArgs e);
      private void dev_rd_btn_CheckedChanged(object sender, EventArgs e)
      {
         if (this.InvokeRequired)
         {
            connectionDelegate cd = new connectionDelegate(dev_rd_btn_CheckedChanged);
            this.Invoke(cd, new object[] { sender, e });
         }
         else
         {
            if ((sender as RadioButton).Checked)
            {
               try
               {
                  Cursor.Current = Cursors.WaitCursor;
                  con_status_pan.BackgroundImage = Properties.Resources.lb_off;
                  Task.Factory.StartNew(() =>
                  {
                     IoTEndpoint mode = IoTEndpoint.dev;
                     if (pilot_rd_btn.Checked)
                        mode = IoTEndpoint.pilot;
                     if (test_rd_btn.Checked)
                        mode = IoTEndpoint.test;
                     if (prod_rd_btn.Checked)
                        mode = IoTEndpoint.prod;

                     this.log_event(_mQTTClient.Connect(mode));
                     if (_mQTTClient.Connected)
                     {
                        con_status_pan.BackgroundImage = Properties.Resources.Green_button;
                        con_lbl_pan.BackgroundImage = Properties.Resources.DEVlbl;
                        if (pilot_rd_btn.Checked)
                           con_lbl_pan.BackgroundImage = Properties.Resources.PILOTlbl;
                        if (test_rd_btn.Checked)
                           con_lbl_pan.BackgroundImage = Properties.Resources.TESTlbl;
                        if (prod_rd_btn.Checked)
                           con_lbl_pan.BackgroundImage = Properties.Resources.PRODlbl;

                        
                     }
                  });
               }
               catch
               {

               }
               finally
               {
                  Cursor.Current = Cursors.Default;
               }
            }
         }
      }

      private void MainWindow_FormClosing(object sender, FormClosingEventArgs e)
      {
         _mQTTClient.Disconnect();
      }

      private delegate void logDelegate(string log);
      private void log_event(string log)
      {
         if (app_log_rtb.InvokeRequired)
         {
            logDelegate ld = new logDelegate(log_event);
            this.Invoke(ld, new object[] { log });
         }
         else
         {
            app_log_rtb.AppendText("\n" + DateTime.Now.ToLongTimeString() + "\t" + log);
            app_log_rtb.SelectionStart = app_log_rtb.Text.Length;
         }
      }

      private delegate void recordDelegate(CradlepointGPSMsg msg);
      private void add_record(CradlepointGPSMsg msg)
      {
         if (record_dgv.InvokeRequired)
         {
            recordDelegate ld = new recordDelegate(add_record);
            this.Invoke(ld, new object[] { msg });
         }
         else
         {
            string lat = (msg.fix.latitude.degree + "°," + msg.fix.latitude.minute + "," + msg.fix.latitude.second);
            string lon = (msg.fix.longitude.degree + "°," + msg.fix.longitude.minute + "," + msg.fix.longitude.second);
            record_dgv.Rows.Add(DateTime.Now.ToString(), sn_txbx.Text, lat, lon, msg.fix.heading, msg.fix.ground_speed_knots, (msg.gpio.pwrIn == 1), (msg.gpio.pwrIn == 1), (msg.gpio.io1 == 1), (msg.gpio.io2 == 1), (msg.gpio.io3 == 1), (msg.gpio.io4 == 1), (msg.gpio.io5 == 1));
         }
      }

      private void send_pan_Click(object sender, EventArgs e)
      {
         if (_mQTTClient.Connected)
         {
            CradlepointGPSMsg gpsmsg = new CradlepointGPSMsg();
            gpsmsg.fix.latitude.degree = (int)lat_deg_num.Value;
            gpsmsg.fix.latitude.minute = (int)lat_min_num.Value;
            gpsmsg.fix.latitude.second = (double)lat_sec_num.Value;

            gpsmsg.fix.longitude.degree = (int)lon_deg_num.Value;
            gpsmsg.fix.longitude.minute = (int)lon_min_num.Value;
            gpsmsg.fix.longitude.second = (double)lon_sec_num.Value;

            gpsmsg.fix.heading = (int)heading_num.Value;
            gpsmsg.fix.ground_speed_knots = (int)speed_num.Value;

            gpsmsg.gpio.pwrIn = Convert.ToInt32(gpioPwnIn_chbx.Checked);
            gpsmsg.gpio.io1 = Convert.ToInt32(gpio1_chbx.Checked);
            gpsmsg.gpio.io2 = Convert.ToInt32(gpio2_chbx.Checked);
            gpsmsg.gpio.io3 = Convert.ToInt32(gpio3_chbx.Checked);
            gpsmsg.gpio.io4 = Convert.ToInt32(gpio4_chbx.Checked);
            gpsmsg.gpio.io5 = Convert.ToInt32(gpio5_chbx.Checked);
            gpsmsg.topic = "CP/GTT/" + (evp_rdo.Checked ? "EVP" : "TSP") + "/" + model_cxbx.SelectedItem.ToString() + "/" + sn_txbx.Text + "/STATE";
            this.log_event(_mQTTClient.Send(gpsmsg));
            this.add_record(gpsmsg);
         }
      }

      #region Visual Controls

      private void send_pan_MouseEnter(object sender, EventArgs e)
      {
      send_pan.BackgroundImage = Properties.Resources.lb_Right_H;
      }

      private void send_pan_MouseLeave(object sender, EventArgs e)
      {
         send_pan.BackgroundImage = Properties.Resources.LB_Right;
      }

      private void send_pan_MouseDown(object sender, MouseEventArgs e)
      {
         send_pan.BackgroundImage = Properties.Resources.LB_Right_off;
      }

      private void send_pan_MouseUp(object sender, MouseEventArgs e)
      {
         send_pan.BackgroundImage = Properties.Resources.lb_Right_H;
      }

      private void dev_icon_pan_MouseEnter(object sender, EventArgs e)
      {
         dev_icon_pan.BackgroundImage = Properties.Resources.Gear___BlueprintsHL;
      }

      private void dev_icon_pan_MouseLeave(object sender, EventArgs e)
      {
         dev_icon_pan.BackgroundImage = Properties.Resources.Gear___Blueprints;
      }

      private void test_icon_pan_MouseEnter(object sender, EventArgs e)
      {
         test_icon_pan.BackgroundImage = Properties.Resources.Gear___BronzeHL;
      }

      private void test_icon_pan_MouseLeave(object sender, EventArgs e)
      {
         test_icon_pan.BackgroundImage = Properties.Resources.Gear___Bronze;
      }

      private void pilot_icon_pan_MouseEnter(object sender, EventArgs e)
      {
         pilot_icon_pan.BackgroundImage = Properties.Resources.Gear_2_0___HL;
      }

      private void pilot_icon_pan_MouseLeave(object sender, EventArgs e)
      {
         pilot_icon_pan.BackgroundImage = Properties.Resources.Gear_2_0;
      }

      private void prod_icon_pan_MouseEnter(object sender, EventArgs e)
      {
         prod_icon_pan.BackgroundImage = Properties.Resources.Gear___GoldHL;
      }

      private void prod_icon_pan_MouseLeave(object sender, EventArgs e)
      {
         prod_icon_pan.BackgroundImage = Properties.Resources.Gear___Gold;
      }

      private void dev_icon_pan_Click(object sender, EventArgs e)
      {
         dev_rd_btn.Checked = true;
      }

      private void test_icon_pan_Click(object sender, EventArgs e)
      {
         test_rd_btn.Checked = true;
      }

      private void pilot_icon_pan_Click(object sender, EventArgs e)
      {
         pilot_rd_btn.Checked = true;
      }

      private void prod_icon_pan_Click(object sender, EventArgs e)
      {
         prod_rd_btn.Checked = true;
      }
      #endregion

   }
}
