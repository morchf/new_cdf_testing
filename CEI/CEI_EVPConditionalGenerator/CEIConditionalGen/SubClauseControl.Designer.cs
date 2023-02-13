
namespace CEIConditionalGen
{
   partial class SubclauseControl
   {
      /// <summary> 
      /// Required designer variable.
      /// </summary>
      private System.ComponentModel.IContainer components = null;

      /// <summary> 
      /// Clean up any resources being used.
      /// </summary>
      /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
      protected override void Dispose(bool disposing)
      {
         if (disposing && (components != null))
         {
            components.Dispose();
         }
         base.Dispose(disposing);
      }

      #region Component Designer generated code

      /// <summary> 
      /// Required method for Designer support - do not modify 
      /// the contents of this method with the code editor.
      /// </summary>
      private void InitializeComponent()
      {
         this.clause_main_tbl = new System.Windows.Forms.TableLayoutPanel();
         this.field_cbo = new System.Windows.Forms.ComboBox();
         this.comp_cbo = new System.Windows.Forms.ComboBox();
         this.clause_value_txbx = new System.Windows.Forms.TextBox();
         this.delete_btn = new System.Windows.Forms.Panel();
         this.clause_main_tbl.SuspendLayout();
         this.SuspendLayout();
         // 
         // clause_main_tbl
         // 
         this.clause_main_tbl.ColumnCount = 7;
         this.clause_main_tbl.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 40F));
         this.clause_main_tbl.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Absolute, 20F));
         this.clause_main_tbl.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 20F));
         this.clause_main_tbl.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Absolute, 20F));
         this.clause_main_tbl.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 40F));
         this.clause_main_tbl.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Absolute, 20F));
         this.clause_main_tbl.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Absolute, 40F));
         this.clause_main_tbl.Controls.Add(this.field_cbo, 0, 0);
         this.clause_main_tbl.Controls.Add(this.comp_cbo, 2, 0);
         this.clause_main_tbl.Controls.Add(this.clause_value_txbx, 4, 0);
         this.clause_main_tbl.Controls.Add(this.delete_btn, 6, 0);
         this.clause_main_tbl.Dock = System.Windows.Forms.DockStyle.Fill;
         this.clause_main_tbl.Location = new System.Drawing.Point(0, 0);
         this.clause_main_tbl.Name = "clause_main_tbl";
         this.clause_main_tbl.RowCount = 1;
         this.clause_main_tbl.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 100F));
         this.clause_main_tbl.Size = new System.Drawing.Size(2095, 53);
         this.clause_main_tbl.TabIndex = 0;
         // 
         // field_cbo
         // 
         this.field_cbo.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Left | System.Windows.Forms.AnchorStyles.Right)));
         this.field_cbo.FormattingEnabled = true;
         this.field_cbo.Items.AddRange(new object[] {
            "CEIIncidentActionDateandTime",
            "CEIIncidentLocationCity",
            "CEIIncidentLocationCoordinates",
            "CEIIncidentLocationCounty",
            "CEIIncidentLocationCrossStreet",
            "CEIIncidentLocationDirections",
            "CEIIncidentLocationName",
            "CEIIncidentLocationState",
            "CEIIncidentLocationStreet1",
            "CEIIncidentLocationStreet2",
            "CEIIncidentLocationZip",
            "CEIIncidentPriority",
            "CEIIncidentStatus",
            "CEIIncidentStatusDateandTime",
            "CEIIncidentTypeCode",
            "CEILastReferenced",
            "CEIUnitID",
            "CEIUnitLocationDateandTime",
            "CEIUnitLocationLatitudeandLongitude",
            "CEIUnitStatus",
            "CEIUnitStatusDateandTime",
            "CEIUnitTypeID",
            "CEIVehicleActive"});
         this.field_cbo.Location = new System.Drawing.Point(3, 6);
         this.field_cbo.Name = "field_cbo";
         this.field_cbo.Size = new System.Drawing.Size(792, 40);
         this.field_cbo.TabIndex = 0;
         // 
         // comp_cbo
         // 
         this.comp_cbo.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Left | System.Windows.Forms.AnchorStyles.Right)));
         this.comp_cbo.FormattingEnabled = true;
         this.comp_cbo.Items.AddRange(new object[] {
            "IS",
            "IS NOT"});
         this.comp_cbo.Location = new System.Drawing.Point(821, 6);
         this.comp_cbo.Name = "comp_cbo";
         this.comp_cbo.Size = new System.Drawing.Size(393, 40);
         this.comp_cbo.TabIndex = 1;
         // 
         // clause_value_txbx
         // 
         this.clause_value_txbx.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Left | System.Windows.Forms.AnchorStyles.Right)));
         this.clause_value_txbx.Location = new System.Drawing.Point(1240, 7);
         this.clause_value_txbx.Name = "clause_value_txbx";
         this.clause_value_txbx.Size = new System.Drawing.Size(792, 39);
         this.clause_value_txbx.TabIndex = 2;
         // 
         // delete_btn
         // 
         this.delete_btn.BackgroundImage = global::CEIConditionalGen.Resources.Delete_32x32;
         this.delete_btn.BackgroundImageLayout = System.Windows.Forms.ImageLayout.Zoom;
         this.delete_btn.Location = new System.Drawing.Point(2055, 0);
         this.delete_btn.Margin = new System.Windows.Forms.Padding(0);
         this.delete_btn.Name = "delete_btn";
         this.delete_btn.Size = new System.Drawing.Size(40, 53);
         this.delete_btn.TabIndex = 3;
         this.delete_btn.DoubleClick += new System.EventHandler(this.delete_btn_DoubleClick);
         // 
         // SubclauseControl
         // 
         this.AutoScaleDimensions = new System.Drawing.SizeF(13F, 32F);
         this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
         this.Controls.Add(this.clause_main_tbl);
         this.Name = "SubclauseControl";
         this.Size = new System.Drawing.Size(2095, 53);
         this.clause_main_tbl.ResumeLayout(false);
         this.clause_main_tbl.PerformLayout();
         this.ResumeLayout(false);

      }

      #endregion

      private System.Windows.Forms.TableLayoutPanel clause_main_tbl;
      private System.Windows.Forms.ComboBox field_cbo;
      private System.Windows.Forms.ComboBox comp_cbo;
      private System.Windows.Forms.TextBox clause_value_txbx;
      private System.Windows.Forms.Panel delete_btn;
   }
}
