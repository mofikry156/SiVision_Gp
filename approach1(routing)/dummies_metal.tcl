set lpp {M1 drawing}

#############################################################################
# the offset from bottom left corner to the middle of the gate {up shift in yll}
##############################################################################
set offset_horzontal_m1_yll_gate 0.15
set m1_offset_yll_s_d 0.423

#############################################################################
# the offset from bottom left corner to the middle of the gate {right shift in xll}
##############################################################################
set offset_horzontal_m1_xll_gate 0.13
set m1_offset_xll_s_d 0.093

##############################################################################
set m1_width 0.034
set m1_span_gate 0.108
#set m1_span_s_d 0.182
set gate_s_d_span 0.359

proc _get_shapes_names {} {
	set insts [db::getInsts -of [ed]]
	set s {}
	db::foreach inst $insts {
		set name [db::getAttr name -of $inst]
		set box  [db::getAttr bBox -of $inst]
		lappend s [list $inst $name $box]
	}
	return $s
}

proc _get_dummeis {get_shapes_names} {
	set k {}
	foreach shape $get_shapes_names {
		set name  [lindex $shape 1]
		set dummy [db::getAttr dummy -of [lindex $shape 0]]
		if {$dummy == 1} {
			lappend k $shape
		}
	}
	return $k
}

proc _create_metals {get_dummeis} {
	foreach dummy $get_dummeis {

		set orient_id [db::getAttr transform -of [lindex $dummy 0]]
		set orient    [db::getAttr orient -of $orient_id]

		if {$orient=="MX"} {

			# ----------------------------
			# MX ORIENT
			# ----------------------------
			set box  [lindex $dummy 2]
			set name [lindex $dummy 1]
			puts "$box of $name"

			set xll_old [lindex $box {1 0}]
			set yll_old [lindex $box {1 1}]

			# gate metal
			set y_ll_new [expr {$yll_old - $::offset_horzontal_m1_yll_gate}]
			set x_ll_new [expr {$xll_old - $::offset_horzontal_m1_xll_gate}]
			set y_ur_new [expr {$y_ll_new - $::m1_width}]
			set x_ur_new [expr {$x_ll_new - $::m1_span_gate}]

			set point_ll  [list $x_ll_new $y_ll_new]
			set point_uur [list $x_ur_new $y_ur_new]
			set bbox      [list $point_ll $point_uur]
			puts "$bbox"

			# s/d metal
			#set y_ll_new_s_d [expr {$yll_old - $::m1_offset_yll_s_d}]
			#set x_ll_new_s_d [expr {$xll_old - $::m1_offset_xll_s_d}]
			#set x_ur_new_s_d [expr {$x_ll_new_s_d - $::m1_span_s_d}]
			#set y_ur_new_s_d [expr {$y_ll_new_s_d - $::m1_width}]

			#set point_ur_s_d [list $x_ur_new_s_d $y_ur_new_s_d]
			#set point_ll_s_d [list $x_ll_new_s_d $y_ll_new_s_d]
			#set box_s_d      [list $point_ll_s_d $point_ur_s_d]

			# gate-to-s/d strap
			# center x of the gate rectangle
			set mid_gate_to_s_d [expr {($x_ll_new + $x_ur_new)/2.0}]

			# make strap width = m1_width (non-zero!)
			set xll_gate_to_s_d [expr {$mid_gate_to_s_d - ($::m1_width/2.0)}]
			set xur_gate_to_s_d [expr {$mid_gate_to_s_d + ($::m1_width/2.0)}]

			set yur_gate_to_s_d [expr {$y_ll_new - $::gate_s_d_span}]
			set point_g_s_ll    [list $xll_gate_to_s_d $y_ll_new]
			set point_g_s_ur    [list $xur_gate_to_s_d $yur_gate_to_s_d]
			set box_g_s_d       [list $point_g_s_ll $point_g_s_ur]

			# create
			le::createRectangle $bbox     -design [ed] -lpp $::lpp
			#le::createRectangle $box_s_d   -design [ed] -lpp $::lpp
			le::createRectangle $box_g_s_d -design [ed] -lpp $::lpp

		} else {

			# ----------------------------
			# NON-MX ORIENT
			# ----------------------------
			set box  [lindex $dummy 2]
			set name [lindex $dummy 1]
			puts "$box of $name"

			set xll_old [lindex $box {0 0}]
			set yll_old [lindex $box {0 1}]

			# gate metal
			set y_ll_new [expr {$yll_old + $::offset_horzontal_m1_yll_gate}]
			set x_ll_new [expr {$xll_old + $::offset_horzontal_m1_xll_gate}]
			set y_ur_new [expr {$y_ll_new + $::m1_width}]
			set x_ur_new [expr {$x_ll_new + $::m1_span_gate}]

			set point_ll  [list $x_ll_new $y_ll_new]
			set point_uur [list $x_ur_new $y_ur_new]
			set bbox      [list $point_ll $point_uur]
			puts "$bbox"

			# s/d metal
			#set y_ll_new_s_d [expr {$yll_old + $::m1_offset_yll_s_d}]
			#set x_ll_new_s_d [expr {$xll_old + $::m1_offset_xll_s_d}]
			#set x_ur_new_s_d [expr {$x_ll_new_s_d + $::m1_span_s_d}]
			#set y_ur_new_s_d [expr {$y_ll_new_s_d + $::m1_width}]

			#set point_ur_s_d [list $x_ur_new_s_d $y_ur_new_s_d]
			#set point_ll_s_d [list $x_ll_new_s_d $y_ll_new_s_d]
			#set box_s_d      [list $point_ll_s_d $point_ur_s_d]

			# gate-to-s/d strap
			set mid_gate_to_s_d [expr {($x_ll_new + $x_ur_new)/2}]
			set xll_gate_to_s_d [expr {($mid_gate_to_s_d - ($::m1_width)/2)}]
			set xur_gate_to_s_d [expr {($mid_gate_to_s_d + ($::m1_width)/2)}]
			set yur_gate_to_s_d [expr {$y_ll_new + $::gate_s_d_span}]

			set point_g_s_ll [list $xll_gate_to_s_d $y_ll_new]
			set point_g_s_ur [list $xur_gate_to_s_d $yur_gate_to_s_d]
			set box_g_s_d    [list $point_g_s_ll $point_g_s_ur]

			# create
			le::createRectangle $bbox     -design [ed] -lpp $::lpp
			#le::createRectangle $box_s_d   -design [ed] -lpp $::lpp
			le::createRectangle $box_g_s_d -design [ed] -lpp $::lpp
		}
	}
}

set get_shapes_names [_get_shapes_names]
set get_dummeis      [_get_dummeis $get_shapes_names]
_create_metals $get_dummeis
