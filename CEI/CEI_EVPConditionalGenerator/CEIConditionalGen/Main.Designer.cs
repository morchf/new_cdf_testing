
namespace CEIConditionalGen
{
   partial class Main
   {
      /// <summary>
      ///  Required designer variable.
      /// </summary>
      private System.ComponentModel.IContainer components = null;

      /// <summary>
      ///  Clean up any resources being used.
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

      #region Windows Form Designer generated code

      /// <summary>
      ///  Required method for Designer support - do not modify
      ///  the contents of this method with the code editor.
      /// </summary>
      private void InitializeComponent()
      {
         this.tableLayoutPanel1 = new System.Windows.Forms.TableLayoutPanel();
         this.clause_rtb = new System.Windows.Forms.RichTextBox();
         this.add_clause_btn = new System.Windows.Forms.Button();
         this.get_conditional_btn = new System.Windows.Forms.Button();
         this.clause_tbl = new System.Windows.Forms.TableLayoutPanel();
         this.clauseGroup1 = new CEIConditionalGen.ClauseGroup();
         this.tableLayoutPanel1.SuspendLayout();
         this.clause_tbl.SuspendLayout();
         this.SuspendLayout();
         // 
         // tableLayoutPanel1
         // 
         this.tableLayoutPanel1.ColumnCount = 3;
         this.tableLayoutPanel1.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Absolute, 20F));
         this.tableLayoutPanel1.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 100F));
         this.tableLayoutPanel1.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Absolute, 20F));
         this.tableLayoutPanel1.Controls.Add(this.clause_rtb, 1, 4);
         this.tableLayoutPanel1.Controls.Add(this.add_clause_btn, 1, 2);
         this.tableLayoutPanel1.Controls.Add(this.get_conditional_btn, 1, 3);
         this.tableLayoutPanel1.Controls.Add(this.clause_tbl, 1, 1);
         this.tableLayoutPanel1.Dock = System.Windows.Forms.DockStyle.Fill;
         this.tableLayoutPanel1.Location = new System.Drawing.Point(0, 0);
         this.tableLayoutPanel1.Name = "tableLayoutPanel1";
         this.tableLayoutPanel1.RowCount = 6;
         this.tableLayoutPanel1.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 20F));
         this.tableLayoutPanel1.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 100F));
         this.tableLayoutPanel1.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 50F));
         this.tableLayoutPanel1.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 50F));
         this.tableLayoutPanel1.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 50F));
         this.tableLayoutPanel1.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 20F));
         this.tableLayoutPanel1.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 20F));
         this.tableLayoutPanel1.Size = new System.Drawing.Size(2272, 1085);
         this.tableLayoutPanel1.TabIndex = 0;
         // 
         // clause_rtb
         // 
         this.clause_rtb.Dock = System.Windows.Forms.DockStyle.Fill;
         this.clause_rtb.Location = new System.Drawing.Point(23, 1018);
         this.clause_rtb.Name = "clause_rtb";
         this.clause_rtb.ReadOnly = true;
         this.clause_rtb.Size = new System.Drawing.Size(2226, 44);
         this.clause_rtb.TabIndex = 0;
         this.clause_rtb.Text = "";
         // 
         // add_clause_btn
         // 
         this.add_clause_btn.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Bottom)));
         this.add_clause_btn.Location = new System.Drawing.Point(1061, 918);
         this.add_clause_btn.Name = "add_clause_btn";
         this.add_clause_btn.Size = new System.Drawing.Size(150, 44);
         this.add_clause_btn.TabIndex = 2;
         this.add_clause_btn.Text = "Add Clause";
         this.add_clause_btn.UseVisualStyleBackColor = true;
         this.add_clause_btn.Click += new System.EventHandler(this.add_clause_btn_Click);
         // 
         // get_conditional_btn
         // 
         this.get_conditional_btn.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Bottom)));
         this.get_conditional_btn.AutoSize = true;
         this.get_conditional_btn.Location = new System.Drawing.Point(1010, 968);
         this.get_conditional_btn.Name = "get_conditional_btn";
         this.get_conditional_btn.Size = new System.Drawing.Size(251, 44);
         this.get_conditional_btn.TabIndex = 3;
         this.get_conditional_btn.Text = "Calculate Conditional";
         this.get_conditional_btn.UseVisualStyleBackColor = true;
         this.get_conditional_btn.Click += new System.EventHandler(this.get_conditional_btn_Click);
         // 
         // clause_tbl
         // 
         this.clause_tbl.AutoScroll = true;
         this.clause_tbl.ColumnCount = 1;
         this.clause_tbl.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 100F));
         this.clause_tbl.Controls.Add(this.clauseGroup1, 0, 0);
         this.clause_tbl.Dock = System.Windows.Forms.DockStyle.Fill;
         this.clause_tbl.Location = new System.Drawing.Point(23, 23);
         this.clause_tbl.Name = "clause_tbl";
         this.clause_tbl.RowCount = 2;
         this.clause_tbl.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 450F));
         this.clause_tbl.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 100F));
         this.clause_tbl.Size = new System.Drawing.Size(2226, 889);
         this.clause_tbl.TabIndex = 4;
         // 
         // clauseGroup1
         // 
         this.clauseGroup1.AutoScroll = true;
         this.clauseGroup1.AutoSize = true;
         this.clauseGroup1.AutoSizeMode = System.Windows.Forms.AutoSizeMode.GrowAndShrink;
         this.clauseGroup1.Dock = System.Windows.Forms.DockStyle.Fill;
         this.clauseGroup1.Location = new System.Drawing.Point(3, 3);
         this.clauseGroup1.Name = "clauseGroup1";
         this.clauseGroup1.Size = new System.Drawing.Size(2220, 444);
         this.clauseGroup1.TabIndex = 0;
         // 
         // Main
         // 
         this.AutoScaleDimensions = new System.Drawing.SizeF(13F, 32F);
         this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
         this.ClientSize = new System.Drawing.Size(2272, 1085);
         this.Controls.Add(this.tableLayoutPanel1);
         this.Name = "Main";
         this.Text = "CEI Conditional  Generator";
         this.tableLayoutPanel1.ResumeLayout(false);
         this.tableLayoutPanel1.PerformLayout();
         this.clause_tbl.ResumeLayout(false);
         this.clause_tbl.PerformLayout();
         this.ResumeLayout(false);

      }

      #endregion

      private System.Windows.Forms.TableLayoutPanel tableLayoutPanel1;
      private System.Windows.Forms.RichTextBox clause_rtb;
      private System.Windows.Forms.Button add_clause_btn;
      private System.Windows.Forms.Button get_conditional_btn;
      private System.Windows.Forms.TableLayoutPanel clause_tbl;
      private ClauseGroup clauseGroup1;
   }
}

