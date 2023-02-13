using Apache.NMS;
using Apache.NMS.ActiveMQ;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Threading;
using System.IO;
using System.Xml.Serialization;

namespace AmazonMQSim
{
   public partial class Main : Form
   {
      private ConnectionFactory _activeMQFactory;
      private IConnection _activeMQConnection;
      private IMessageProducer _activeMQPRMProducer;
      private ISession _activeMQSession;
      List<DemoEntry> items = new List<DemoEntry>();

      public Main()
      {
         InitializeComponent();
         rando_btn_Click(this, null);
         con_status_pan_Click(this, null);

      }

      private void con_status_pan_Enter(object sender, EventArgs e)
      {
         if (!send_pan.Enabled)
            con_status_pan.BackgroundImage = Properties.Resources.LB_power;
         else
            con_status_pan.BackgroundImage = Properties.Resources.LB_power_H;
         con_status_pan.Refresh();
      }

      private void con_status_pan_Leave(object sender, EventArgs e)
      {
         if (!send_pan.Enabled)
            con_status_pan.BackgroundImage = Properties.Resources.LB_power_off;
         else
            con_status_pan.BackgroundImage = Properties.Resources.LB_power;
         con_status_pan.Refresh();
      }

      private void con_status_pan_Click(object sender, EventArgs e)
      {
         _activeMQFactory = new ConnectionFactory(endpoint_txbx.Text);
         if (_activeMQConnection == null || !_activeMQConnection.IsStarted)
         {
            try
            {
               Cursor.Current = Cursors.WaitCursor;
               _activeMQConnection = _activeMQFactory.CreateConnection(user_txbx.Text, pass_txbx.Text);
               _activeMQConnection.Start();
               _activeMQConnection.ExceptionListener += _activeMQConnection_ExceptionListener;
               _activeMQSession = _activeMQConnection.CreateSession(AcknowledgementMode.AutoAcknowledge);
               con_status_pan.BackgroundImage = Properties.Resources.LB_power;
               con_status_pan.Refresh();
               send_pan.Enabled = true;
               scale_pan.Enabled = true;
               send_pan.BackgroundImage = Properties.Resources.LB_Right;
            }
            catch (Exception ex)
            {
               Cursor.Current = Cursors.Default;
               MessageBox.Show(ex.ToString(), "Connection Error", MessageBoxButtons.OK, MessageBoxIcon.Error, MessageBoxDefaultButton.Button1);
            }
            finally
            {
               Cursor.Current = Cursors.Default;
            }
         }
         else
         {
            _activeMQConnection.Stop();
            _activeMQConnection.ExceptionListener -= _activeMQConnection_ExceptionListener;
            send_pan.Enabled = false;
            scale_pan.Enabled = false;
            send_pan.BackgroundImage = Properties.Resources.LB_Right_off;

            con_status_pan.BackgroundImage = Properties.Resources.LB_power_off;
            con_status_pan.Refresh();
         }
      }

      private void _activeMQConnection_ExceptionListener(Exception exception)
      {
         try
         {
            if (_activeMQPRMProducer != null)
            {
               _activeMQPRMProducer.Close();
            }
         }
         catch (Exception)
         { }
         try
         {
            if (_activeMQSession != null)
            {
               _activeMQSession.Close();
            }
         }
         catch (Exception)
         { }

         if (_activeMQConnection != null)
         {
            try
            {
               _activeMQConnection.ExceptionListener -= _activeMQConnection_ExceptionListener;
               _activeMQConnection.Close();
            }
            catch (Exception)
            {
            }
         }
         _activeMQConnection = null;
         _activeMQPRMProducer = null;
      }

      private void Main_FormClosing(object sender, FormClosingEventArgs e)
      {
         if (_activeMQConnection != null)
         {
            try
            {
               _activeMQConnection.ExceptionListener -= _activeMQConnection_ExceptionListener;
               _activeMQConnection.Close();
            }
            catch (Exception)
            {
            }
         }
      }

      delegate void DelegateReport(object[] args);
      private void InvokeReport(object[] args)
      {
         if (record_dgv.InvokeRequired)
         {
            DelegateReport d = new DelegateReport(InvokeReport);
            this.Invoke(d, new object[] { args });
         }
         else
         {
            record_dgv.Rows.Add(args);
         }
      }


      public void send_random(string vehicle)
      {
         try
         {
            VehicleMessage message = new VehicleMessage();
            message.messageId = Guid.NewGuid().ToString();
            Random rand = new Random();



            message.gps = new gps();
            message.gps.latitude = "5.000000";
            message.gps.longitude = "5.000000";
            message.gps.direction = rand.Next(0, 360).ToString();
            //message.gps.latitude = rand.Next(-90, 90) + "." + rand.Next(0, 9) + rand.Next(0, 9) + rand.Next(0, 9) + rand.Next(0, 9) + rand.Next(0, 9) + rand.Next(0, 9);
            message.gps.speed = rand.Next(1, 160).ToString();
            //message.gps.longitude = rand.Next(-90, 90) + "." + rand.Next(0, 9) + rand.Next(0, 9) + rand.Next(0, 9) + rand.Next(0, 9) + rand.Next(0, 9) + rand.Next(0, 9);
            message.enable = "True";
            message.disable = rand.Next(0, 1) > 0 ? "True" : "False";

            int turnsignal = rand.Next(0, 3);
            switch (turnsignal)
               {
               case 0:
                  message.turnSignal = "None";
                  break;
               case 1:
                  message.turnSignal = "Left";
                  break;
               case 2:
                  message.turnSignal = "Right";
                  break;
               case 3:
                  message.turnSignal = "Both";
                  break;
            }
            string msg = JsonConvert.SerializeObject(message);

            string queue = "WHELEN." + vehicle + ".GTT.SCP.RTVEHDATA";
            IDestination prmDest = _activeMQSession.GetQueue(queue);
            _activeMQPRMProducer = _activeMQSession.CreateProducer(prmDest);
            _activeMQPRMProducer.DeliveryMode = MsgDeliveryMode.NonPersistent;

            _activeMQPRMProducer.Send(_activeMQSession.CreateTextMessage(msg));


            //record_dgv.Rows.Add(DateTime.Now.ToString(), message.messageId, message.messageId, message.gps.direction, message.gps.speed, message.gps.latitude, message.gps.longitude, message.turnSignal, en_chk.Checked, dis_chk.Checked);
            object[] report = { DateTime.Now.Ticks.ToString(), vehicle, message.messageId, message.gps.direction, message.gps.speed, message.gps.latitude, message.gps.longitude, message.turnSignal, message.enable == "True", message.disable == "True" };
            InvokeReport(report);

         }
         catch (Exception ex)
         {
            //MessageBox.Show(ex.ToString(), "Connection Error", MessageBoxButtons.OK, MessageBoxIcon.Error, MessageBoxDefaultButton.Button1);
         }
      }

      private void RunScale(messageSet ms)
      {
         int msgCount = ms.count;
         while (msgCount > 0)
         {
            send_random(ms.vehId);
            Thread.Sleep(500);
            msgCount--;
         }
      }


      private void panel1_Click(object sender, EventArgs e)
      {
         Cursor.Current = Cursors.WaitCursor;
         try
         {
            VehicleMessage message = new VehicleMessage();
            message.messageId = msg_id_tbxb.Text;
            //message.vehicleId = veh_id_txbx.Text;
            message.gps = new gps();
            message.gps.direction = direction_num.Value.ToString();
            message.gps.latitude = lat_num.Value.ToString();
            message.gps.speed = speed_num.Value.ToString();
            message.gps.longitude = long_num.Value.ToString();
            message.enable = en_chk.Checked ? "True" : "False";
            message.disable = dis_chk.Checked ? "True" : "False";
            message.turnSignal = "None";
            message.turnSignal = both_rtb.Checked ? "Both" : message.turnSignal;
            message.turnSignal = left_rdo.Checked ? "Left" : message.turnSignal;
            message.turnSignal = right_rdo.Checked ? "Right" : message.turnSignal;
            string msg = JsonConvert.SerializeObject(message);

            string queue = "WHELEN." + veh_id_txbx.Text.Replace(" ", "") + ".GTT.SCP.RTVEHDATA";
            IDestination prmDest = _activeMQSession.GetQueue(queue);
            _activeMQPRMProducer = _activeMQSession.CreateProducer(prmDest);
            _activeMQPRMProducer.DeliveryMode = MsgDeliveryMode.NonPersistent;

            _activeMQPRMProducer.Send(_activeMQSession.CreateTextMessage(msg));


            record_dgv.Rows.Add(DateTime.Now.ToString(), veh_id_txbx.Text.Replace(" ", ""), message.messageId, message.gps.direction, message.gps.speed, message.gps.latitude, message.gps.longitude, message.turnSignal, en_chk.Checked, dis_chk.Checked);
         }
         catch (Exception ex)
         {
            MessageBox.Show(ex.ToString(), "Connection Error", MessageBoxButtons.OK, MessageBoxIcon.Error, MessageBoxDefaultButton.Button1);
         }
         finally
         {
            this.rando_btn_Click(this, null);
            Cursor.Current = Cursors.Default;
         }
      }

      private void rando_btn_Click(object sender, EventArgs e)
      {
         msg_id_tbxb.Text=Guid.NewGuid().ToString();
         
      }

      private void send_pan_MouseEnter(object sender, EventArgs e)
      {
         if (send_pan.Enabled)
         {
            send_pan.BackgroundImage = Properties.Resources.lb_Right_H;
         }
      }

      private void send_pan_MouseLeave(object sender, EventArgs e)
      {
         if (send_pan.Enabled)
         {
            send_pan.BackgroundImage = Properties.Resources.LB_Right;
         }
      }

      private void rando_btn_MouseEnter(object sender, EventArgs e)
      {
         rando_btn.BackgroundImage = Properties.Resources.LB_FastForward_H;
      }

      private void rando_btn_MouseLeave(object sender, EventArgs e)
      {
         rando_btn.BackgroundImage = Properties.Resources.LB_FastForward;
      }

      private void con_status_pan_MouseDown(object sender, MouseEventArgs e)
      {
         if (con_status_pan.BackgroundImage == Properties.Resources.LB_power_H)
            con_status_pan.BackgroundImage = Properties.Resources.LB_power;
         else
            con_status_pan.BackgroundImage = Properties.Resources.LB_power_H;

         con_status_pan.Refresh();
      }

      private void con_status_pan_MouseUp(object sender, MouseEventArgs e)
      {
         if (!send_pan.Enabled)
            con_status_pan.BackgroundImage = Properties.Resources.LB_power_off;
         else
            con_status_pan.BackgroundImage = Properties.Resources.LB_power_H;
         con_status_pan.Refresh();
      }

      private void con_status_pan_MouseClick(object sender, MouseEventArgs e)
      {
         if (!send_pan.Enabled)
            con_status_pan.BackgroundImage = Properties.Resources.LB_power;
         else
            con_status_pan.BackgroundImage = Properties.Resources.LB_power_H;
         con_status_pan.Refresh();
      }

      private void reset_pan_MouseEnter(object sender, EventArgs e)
      {
         reset_pan.BackgroundImage = Properties.Resources.Rotate_CW_hot;
      }

      private void reset_pan_MouseLeave(object sender, EventArgs e)
      {
         reset_pan.BackgroundImage = Properties.Resources.Rotate_CW;
      }

      private void reset_pan_Click(object sender, EventArgs e)
      {
         if (MessageBox.Show("Clear Record?", "", MessageBoxButtons.OKCancel) == DialogResult.OK)
         {
            record_dgv.Rows.Clear();
         }
      }

      private void scale_pan_MouseEnter(object sender, EventArgs e)
      {
         if (send_pan.Enabled)
         {
            scale_pan.BackgroundImage = Properties.Resources.lb_Right_H;
         }
      }

      private void scale_pan_MouseLeave(object sender, EventArgs e)
      {
         if (send_pan.Enabled)
         {
            scale_pan.BackgroundImage = Properties.Resources.LB_Right;
         }
      }

      private void scale_pan_Click(object sender, EventArgs e)
      {
         int threadCount = (int)num_veh_num.Value;
         int msgCount = (int)num_msg_num.Value;

         int[] array = new int[threadCount];

         int idx = 0;
         while (msgCount > 0)
         {
            array[idx]++;
            idx++;
            if (idx == array.Length)
            {
               idx = 0;
            }
            msgCount--;
         }

         string res = "";
         List<messageSet> msgs = new List<messageSet>();
         List<int> list = new List<int>();
         list.AddRange(array);
         idx = 0;
         foreach (int s in list)
         {
            res += "whelenCom" + idx + ": " + s + " messages \r\n";
            msgs.Add(new messageSet(s, "whelenCom" + idx));
            idx++;
         }
         idx = 0;
         DateTime start = DateTime.Now;
         if (MessageBox.Show(res, "Divisions", MessageBoxButtons.OKCancel, MessageBoxIcon.Information, MessageBoxDefaultButton.Button1) == DialogResult.OK)
         { 
            Cursor.Current = Cursors.WaitCursor;
            foreach (messageSet s in msgs)
            {
               Thread t = new Thread(() => RunScale(s));
               t.Start();
            }
         }
      Cursor.Current = Cursors.Default;
      }

      private void browse_pan_Click(object sender, EventArgs e)
      {
         OpenFileDialog m_openFileDialog = new OpenFileDialog();
         string extension = ".json";
         m_openFileDialog.DefaultExt = extension;
         DateTime now = DateTime.Now;
         string name = "Autorun Config-" + now.ToString("g");
         char[] badChars = Path.GetInvalidFileNameChars();
         foreach (char badchar in badChars)
         {
            name = name.Replace(badchar, '_');
         }

         if (m_openFileDialog.ShowDialog() == DialogResult.OK)
         {
            demo_file_txbx.Text = m_openFileDialog.FileName;
            using (StreamReader sr = new StreamReader(m_openFileDialog.FileName))
            {
               string json = sr.ReadToEnd();
               file_sum_txbx.Text = json;
               items = JsonConvert.DeserializeObject<List<DemoEntry>>(json);
            }
            run_demo_pan.Enabled = true;
            run_demo_pan.BackgroundImage = Properties.Resources.LB_Right;
          }
      }


      private void browse_pan_MouseEnter(object sender, EventArgs e)
      {
         browse_pan.BackgroundImage = Properties.Resources.Open_32x32_hot;
      }

      private void browse_pan_MouseLeave(object sender, EventArgs e)
      {
         browse_pan.BackgroundImage = Properties.Resources.Open_32x32;
      }

      private void run_demo_pan_MouseEnter(object sender, EventArgs e)
      {
         if (run_demo_pan.Enabled)
         {
            run_demo_pan.BackgroundImage = Properties.Resources.lb_Right_H;
         }
      }

      private void run_demo_pan_MouseLeave(object sender, EventArgs e)
      {
         if (run_demo_pan.Enabled)
         {
            run_demo_pan.BackgroundImage = Properties.Resources.LB_Right;
         }
      }

      private void run_demo_pan_Click(object sender, EventArgs e)
      {
         List<VehicleMessage> vms = new List<VehicleMessage>();
         foreach (DemoEntry d in items)
         {
            VehicleMessage v = new VehicleMessage();
            v.messageId = Guid.NewGuid().ToString();
            v.gps = d.gps;
            v.disable = d.disable;
            v.enable = d.enable;
            v.turnSignal = d.turnSignal;
            vms.Add(v);
         }
         foreach (VehicleMessage message in vms)
         {
            string veh_id = items[vms.IndexOf(message)].vehicleId;
            string queue = "WHELEN." + veh_id + ".GTT.SCP.RTVEHDATA";
            IDestination prmDest = _activeMQSession.GetQueue(queue);
            _activeMQPRMProducer = _activeMQSession.CreateProducer(prmDest);
            _activeMQPRMProducer.DeliveryMode = MsgDeliveryMode.NonPersistent;
            string msg = JsonConvert.SerializeObject(message);
            _activeMQPRMProducer.Send(_activeMQSession.CreateTextMessage(msg));


            record_dgv.Rows.Add(DateTime.Now.ToString(), veh_id, 
               message.messageId, message.gps.direction, message.gps.speed, message.gps.latitude, 
               message.gps.longitude, message.turnSignal, message.enable == "True", message.enable == "True");
            Thread.Sleep(1000);
         }
      }
   }
}

public class messageSet
{
   public int count;
   public string vehId;

   public messageSet(int msgs, string id)
   {
      count = msgs;
      vehId = id;
   }
}

public class VehicleMessage
{
   public string messageId { get; set; }
   //public string vehicleId { get; set; }
   public string dateTime { get
      { return DateTime.Now.ToString(); }
       }
   public gps gps { get; set; }
   public string turnSignal { get; set; }
   public string enable { get; set; }
   public string disable { get; set; }

}

public class gps
{
   public string direction { get; set; }
   public string speed { get; set; }
   public string latitude { get; set; }
   public string longitude { get; set; }
}

public class DemoEntry
{
   public string vehicleId { get; set; }
   public gps gps { get; set; }
   public string turnSignal { get; set; }
   public string enable { get; set; }
   public string disable { get; set; }
}

