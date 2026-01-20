##############this script is responsible for outputing coordinates and for outputing the height and width of the 5tota#################
set ctx    [de::getActiveContext]
set design [db::getAttr editDesign -of $ctx]

# ADD THIS:
set insts  [db::getAttr insts -of $design]
puts "inst count = [db::getCount $insts]"

puts "design = $design"
puts "design type = [db::getAttr type -of $design]"

set fp [open "/home/users/svgplayout2601mofikry/gonna_work/1st_script_op.txt" "w"]
puts $fp [format "%-22s %10s %10s %10s %10s %10s %10s" \
              "INST_NAME" "ORIGIN_X" "ORIGIN_Y" "BBOX_LL_X" "BBOX_LL_Y" "BBOX_UR_X" "BBOX_UR_Y"]


set first 1
set minX 0
set minY 0
set maxX 0
set maxY 0

db::foreach inst $insts {
    set n  "<noname>"
    set bb ""
    set org ""

    catch { set n   [db::getAttr name   -of $inst] }
    catch { set bb  [db::getAttr bBox   -of $inst] }
    catch { set org [db::getAttr origin -of $inst] }

    # Parse origin
    if {$org ne ""} {
        set ox [lindex $org 0]
        set oy [lindex $org 1]
    } else {
        set ox ""; set oy ""
    }

    # Parse bbox
    if {$bb ne ""} {
        set ll [lindex $bb 0]
        set ur [lindex $bb 1]
        set llx [lindex $ll 0]
        set lly [lindex $ll 1]
        set urx [lindex $ur 0]
        set ury [lindex $ur 1]

        # Update overall bbox
        if {$first} {
            set minX $llx
            set minY $lly
            set maxX $urx
            set maxY $ury
            set first 0
        } else {
            if {$llx < $minX} { set minX $llx }
            if {$lly < $minY} { set minY $lly }
            if {$urx > $maxX} { set maxX $urx }
            if {$ury > $maxY} { set maxY $ury }
        }
    } else {
        set llx ""; set lly ""; set urx ""; set ury ""
    }

    puts $fp [format "%-22s %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f" \
             $n $ox $oy $llx $lly $urx $ury]

}

# Compute width/height
set width  [expr {$maxX - $minX}]
set height [expr {$maxY - $minY}]

puts $fp ""
puts $fp "# OTA_BOTTOM_LEFT = ($minX, $minY)"
puts $fp "# OTA_TOP_RIGHT   = ($maxX, $maxY)"
puts $fp "# OTA_WIDTH       = $width"
puts $fp "# OTA_HEIGHT      = $height"

close $fp
puts "Instance coordinates + OTA size written successfully"

