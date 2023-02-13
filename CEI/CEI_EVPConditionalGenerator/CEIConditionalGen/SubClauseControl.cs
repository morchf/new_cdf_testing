using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Text;
using System.Windows.Forms;

namespace CEIConditionalGen
{
   public partial class SubclauseControl : UserControl
   {
      public string clauseName = "clause0";
      public SubclauseControl()
      {
         InitializeComponent();
         field_cbo.SelectedIndex = 0;
         comp_cbo.SelectedIndex = 0;
      }

      public string return_sub_clauses()
      {
         string subclause = "";
         string[] values = clause_value_txbx.Text.Split(',');
         for (int x = 0; x < values.Length; x++)
         {
            string op = (comp_cbo.SelectedItem.ToString() == "IS" ? "==" : "!=");
            subclause = subclause + "(\"" + field_cbo.SelectedItem.ToString() + "\" " + op + " \"" + values[x] + "\")";
            if ((x + 1) < values.Length)
               subclause = subclause + " or ";
         }
         return "(" + subclause + ")";
      }

      private void delete_btn_DoubleClick(object sender, EventArgs e)
      {
         (this.Parent.Parent.Parent.Parent as ClauseGroup).remove_clause(this);
      }
   }
}
