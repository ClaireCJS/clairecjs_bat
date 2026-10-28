using System; using System.Drawing; using System.Drawing.Imaging; using System.IO; using System.Reflection; using System.Windows.Forms; using PAFPlayerScreenSaver;
class FooterTests {
 static Control Find(Control root,string text) { foreach(Control c in root.Controls) {if(c is Button && c.Text==text)return c;var found=Find(c,text);if(found!=null)return found;}return null; }
 [STAThread] static int Main(string[] args) { try {
 Native.EnableDpiAwareness();Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);
 ConfigStore.OverridePath=Path.Combine(args[0],"fixture.cfg"); int checks=0;
 foreach(float fontSize in new[]{10f,15f,20f}) foreach(float scale in new[]{1f,1.5f,2f}) {
 using(var form=new SettingsForm(new Options{Port=1})) {
 form.StartPosition=FormStartPosition.Manual;form.Location=new Point(-30000,-30000);form.ShowInTaskbar=false;
 form.Font=new Font("Segoe UI",fontSize);form.Show();
 var flags=BindingFlags.Instance|BindingFlags.NonPublic;
 ((System.Windows.Forms.Timer)typeof(SettingsForm).GetField("timer",flags).GetValue(form)).Stop();
 ((Label)typeof(SettingsForm).GetField("status",flags).GetValue(form)).Text="Settings file: C:\\a long folder path\\a long folder path\\PAFPlayer\\screensaver\\PAFPlayer.cfg\n"+new string('W',180);
 form.Scale(new SizeF(scale,scale));form.ClientSize=new Size((int)(530*scale),(int)(335*scale));form.PerformLayout();Application.DoEvents();
 foreach(string text in new[]{"Apply","OK","Cancel"}) {
 Control button=Find(form,text); if(button==null || !button.Visible)throw new Exception(text+" missing");
 Rectangle box=button.RectangleToScreen(button.ClientRectangle);
 for(Control parent=button.Parent;parent!=null;parent=parent.Parent)if(!parent.RectangleToScreen(parent.ClientRectangle).Contains(box))throw new Exception(text+" clipped: font="+fontSize+" scale="+scale+" parent="+parent.GetType().Name+" bounds="+box+" parentBounds="+parent.RectangleToScreen(parent.ClientRectangle));
 checks++;
 }
 using(var shot=new Bitmap(form.Width,form.Height)){form.DrawToBitmap(shot,new Rectangle(Point.Empty,form.Size));shot.Save(Path.Combine(args[0],"footer-"+fontSize+"-"+scale+".png"),ImageFormat.Png);}
 form.Close();
 }
 }
 Console.WriteLine("PASS "+checks+" button visibility checks across font sizes and scaling");return 0;
 }catch(Exception e){Console.WriteLine(e);return 1;} }
}
