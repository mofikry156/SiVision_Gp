# Master Execution Script
# Auto-generated - executes all routing automation scripts in order
# Output Directory: c:\Users\TEBA\Desktop\automated automation

puts "==========================================================="
puts "VLSI Routing Automation - Master Execution"
puts "==========================================================="

# Step 1: 1_dummies_connections.tcl
puts "Executing step 1/6: 1_dummies_connections.tcl"
source "c:/Users/TEBA/Desktop/automated automation/1_dummies_connections.tcl"
puts "Completed: 1_dummies_connections.tcl"

# Step 2: 2_pocut.tcl
puts "Executing step 2/6: 2_pocut.tcl"
source "c:/Users/TEBA/Desktop/automated automation/2_pocut.tcl"
puts "Completed: 2_pocut.tcl"

# Step 3: 3_metal2.tcl
puts "Executing step 3/6: 3_metal2.tcl"
source "c:/Users/TEBA/Desktop/automated automation/3_metal2.tcl"
puts "Completed: 3_metal2.tcl"

# Step 4: 4_taps_routing.tcl
puts "Executing step 4/6: 4_taps_routing.tcl"
source "c:/Users/TEBA/Desktop/automated automation/4_taps_routing.tcl"
puts "Completed: 4_taps_routing.tcl"

# Step 5: 5_via12.tcl
puts "Executing step 5/6: 5_via12.tcl"
source "c:/Users/TEBA/Desktop/automated automation/5_via12.tcl"
puts "Completed: 5_via12.tcl"

# Step 6: 6_via23_metal3.tcl
puts "Executing step 6/6: 6_via23_metal3.tcl"
source "c:/Users/TEBA/Desktop/automated automation/6_via23_metal3.tcl"
puts "Completed: 6_via23_metal3.tcl"

puts "==========================================================="
puts "All routing automation steps completed successfully!"
puts "==========================================================="