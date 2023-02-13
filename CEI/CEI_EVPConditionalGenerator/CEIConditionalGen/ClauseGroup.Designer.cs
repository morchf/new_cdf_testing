
namespace CEIConditionalGen
{
   partial class ClauseGroup
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
         this.main_tbl = new System.Windows.Forms.TableLayoutPanel();
         this.add_subclause = new System.Windows.Forms.Button();
         this.clauses_tbl = new System.Windows.Forms.TableLayoutPanel();
         this.clauseControl1 = new CEIConditionalGen.SubclauseControl();
         this.groupBox1 = new System.Windows.Forms.GroupBox();
         this.delete_btn = new System.Windows.Forms.Panel();
         this.main_tbl.SuspendLayout();
         this.clauses_tbl.SuspendLayout();
         this.groupBox1.SuspendLayout();
         this.SuspendLayout();
         // 
         // main_tbl
         // 
         this.main_tbl.ColumnCount = 4;
         this.main_tbl.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Absolute, 20F));
         this.main_tbl.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 100F));
         this.main_tbl.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Absolute, 40F));
         this.main_tbl.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Absolute, 20F));
         this.main_tbl.Controls.Add(this.add_subclause, 1, 1);
         this.main_tbl.Controls.Add(this.clauses_tbl, 1, 0);
         this.main_tbl.Controls.Add(this.delete_btn, 2, 1);
         this.main_tbl.Dock = System.Windows.Forms.DockStyle.Fill;
         this.main_tbl.Location = new System.Drawing.Point(3, 35);
         this.main_tbl.Name = "main_tbl";
         this.main_tbl.RowCount = 2;
         this.main_tbl.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 100F));
         this.main_tbl.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 50F));
         this.main_tbl.Size = new System.Drawing.Size(2352, 902);
         this.main_tbl.TabIndex = 0;
         // 
         // add_subclause
         // 
         this.add_subclause.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Bottom)));
         this.add_subclause.AutoSize = true;
         this.add_subclause.AutoSizeMode = System.Windows.Forms.AutoSizeMode.GrowAndShrink;
         this.add_subclause.Image = global::CEIConditionalGen.Resources.Blue_Bus___Copy;
         this.add_subclause.ImageAlign = System.Drawing.ContentAlignment.MiddleLeft;
         this.add_subclause.Location = new System.Drawing.Point(1044, 855);
         this.add_subclause.Name = "add_subclause";
         this.add_subclause.Size = new System.Drawing.Size(223, 44);
         this.add_subclause.TabIndex = 0;
         this.add_subclause.Text = "    Add Sub-Clause";
         this.add_subclause.UseVisualStyleBackColor = true;
         this.add_subclause.Click += new System.EventHandler(this.add_subclause_Click);
         // 
         // clauses_tbl
         // 
         this.clauses_tbl.AutoScroll = true;
         this.clauses_tbl.ColumnCount = 1;
         this.main_tbl.SetColumnSpan(this.clauses_tbl, 2);
         this.clauses_tbl.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 100F));
         this.clauses_tbl.Controls.Add(this.clauseControl1, 0, 0);
         this.clauses_tbl.Dock = System.Windows.Forms.DockStyle.Fill;
         this.clauses_tbl.Location = new System.Drawing.Point(23, 3);
         this.clauses_tbl.Name = "clauses_tbl";
         this.clauses_tbl.RowCount = 2;
         this.clauses_tbl.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 50F));
         this.clauses_tbl.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 100F));
         this.clauses_tbl.Size = new System.Drawing.Size(2306, 846);
         this.clauses_tbl.TabIndex = 1;
         // 
         // clauseControl1
         // 
         this.clauseControl1.Location = new System.Drawing.Point(3, 3);
         this.clauseControl1.Name = "clauseControl1";
         this.clauseControl1.Size = new System.Drawing.Size(2300, 44);
         this.clauseControl1.TabIndex = 0;
         // 
         // groupBox1
         // 
         this.groupBox1.Controls.Add(this.main_tbl);
         this.groupBox1.Dock = System.Windows.Forms.DockStyle.Fill;
         this.groupBox1.Location = new System.Drawing.Point(0, 0);
         this.groupBox1.Name = "groupBox1";
         this.groupBox1.Size = new System.Drawing.Size(2358, 940);
         this.groupBox1.TabIndex = 1;
         this.groupBox1.TabStop = false;
         // 
         // delete_btn
         // 
         this.delete_btn.BackgroundImage = global::CEIConditionalGen.Resources.Delete_32x32;
         this.delete_btn.BackgroundImageLayout = System.Windows.Forms.ImageLayout.Zoom;
         this.delete_btn.Location = new System.Drawing.Point(2292, 852);
         this.delete_btn.Margin = new System.Windows.Forms.Padding(0);
         this.delete_btn.Name = "delete_btn";
         this.delete_btn.Size = new System.Drawing.Size(40, 50);
         this.delete_btn.TabIndex = 4;
         this.delete_btn.DoubleClick += new System.EventHandler(this.delete_btn_DoubleClick);
         // 
         // ClauseGroup
         // 
         this.AutoScaleDimensions = new System.Drawing.SizeF(13F, 32F);
         this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
         this.Controls.Add(this.groupBox1);
         this.Name = "ClauseGroup";
         this.Size = new System.Drawing.Size(2358, 940);
         this.main_tbl.ResumeLayout(false);
         this.main_tbl.PerformLayout();
         this.clauses_tbl.ResumeLayout(false);
         this.groupBox1.ResumeLayout(false);
         this.ResumeLayout(false);

      }

      #endregion

      private System.Windows.Forms.TableLayoutPanel main_tbl;
      private System.Windows.Forms.Button add_subclause;
      private System.Windows.Forms.TableLayoutPanel clauses_tbl;
      private SubclauseControl clauseControl1;
      private System.Windows.Forms.GroupBox groupBox1;
      private System.Windows.Forms.Panel delete_btn;
   }
}
