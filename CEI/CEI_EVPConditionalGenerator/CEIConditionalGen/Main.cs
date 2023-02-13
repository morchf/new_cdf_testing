using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace CEIConditionalGen
{
   public partial class Main : Form
   {
      public Main()
      {
         InitializeComponent();
      }

      private void add_clause_btn_Click(object sender, EventArgs e)
      {
         clause_tbl.RowStyles.RemoveAt(clause_tbl.RowStyles.Count - 1);
         int current_clauses = clause_tbl.RowCount;
         clause_tbl.RowStyles.Add(new RowStyle(SizeType.Absolute, 50F));
         ComboBox clauseBox = new ComboBox();
         clauseBox.Items.Add("and");
         clauseBox.Items.Add("or");
         clauseBox.SelectedIndex = 0;
         clause_tbl.Controls.Add(clauseBox);
         clauseBox.Anchor = AnchorStyles.Top | AnchorStyles.Bottom;
         clause_tbl.RowStyles.Add(new RowStyle(SizeType.Absolute, 450F));
         ClauseGroup cg = new ClauseGroup();
         clause_tbl.Controls.Add(cg);
         cg.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
         clause_tbl.RowStyles.Add(new RowStyle(SizeType.Percent, 100F));
      }

      private void get_conditional_btn_Click(object sender, EventArgs e)
      {
         string clause = "";
         foreach (Control c in clause_tbl.Controls)
         {
            if (c is ClauseGroup)
            {
               clause = clause + (c as ClauseGroup).return_clauses();
            }
            else if (c is ComboBox)
            {
               clause = clause + " " + (c as ComboBox).SelectedItem.ToString() + " ";
            }
         }
         clause_rtb.Text = "(" + clause + ")".Replace("( ", "(").Replace(" ", "");
      }

      public void remove_clause(ClauseGroup cg)
      {
         int idx = 0;
         for (int x = 0; x < clause_tbl.Controls.Count; x++)
         {
            if (clause_tbl.Controls[x] == cg)
            {
               idx = x;
            }
         }
         if (idx != 0)
         {
            clause_tbl.Controls.Remove(clause_tbl.Controls[idx - 1]);
            clause_tbl.Controls.Remove(cg);
            clause_tbl.Refresh();
         }
      }
   }
}
