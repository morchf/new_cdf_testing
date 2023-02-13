using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Text;
using System.Windows.Forms;

namespace CEIConditionalGen
{
   public partial class ClauseGroup : UserControl
   {
      public ClauseGroup()
      {
         InitializeComponent();
      }

      private void add_subclause_Click(object sender, EventArgs e)
      {
         clauses_tbl.RowStyles.RemoveAt(clauses_tbl.RowStyles.Count-1);
         int current_clauses = clauses_tbl.RowCount;
         clauses_tbl.RowStyles.Add(new RowStyle(SizeType.Absolute, 50F));
         ComboBox clauseBox = new ComboBox();
         clauseBox.Items.Add("and");
         clauseBox.Items.Add("or");
         clauseBox.SelectedIndex = 0;
         clauses_tbl.Controls.Add(clauseBox);
         clauseBox.Anchor = AnchorStyles.Top | AnchorStyles.Bottom;
         clauses_tbl.RowStyles.Add(new RowStyle(SizeType.Absolute, 50F));
         SubclauseControl cc = new SubclauseControl();
         clauses_tbl.Controls.Add(cc);
         cc.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
         clauses_tbl.RowStyles.Add(new RowStyle(SizeType.Percent,100F));
      }

      public void remove_clause(SubclauseControl cc)
      {
         int idx = 0;
         for (int x = 0; x < clauses_tbl.Controls.Count; x++)
         {
            if (clauses_tbl.Controls[x] == cc)
            {
               idx = x;
            }
         }
         if (idx != 0)
         {
            clauses_tbl.Controls.Remove(clauses_tbl.Controls[idx - 1]);
            clauses_tbl.Controls.Remove(cc);
            clauses_tbl.Refresh();
         }
      }


      public string return_clauses()
      {
         string clause = "";
         foreach (Control c in clauses_tbl.Controls)
         {
            if (c is SubclauseControl)
            {
               clause = clause + (c as SubclauseControl).return_sub_clauses();
            }
            else if (c is ComboBox)
            {
               clause = clause + " " + (c as ComboBox).SelectedItem.ToString() + " ";
            }
         }
         return "(" + clause + ")";
      }

      private void delete_btn_DoubleClick(object sender, EventArgs e)
      {
         (this.Parent.Parent.Parent as Main).remove_clause(this);
      }
   }
}
