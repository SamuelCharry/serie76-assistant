package com.serie76.assistant.ui

import com.serie76.assistant.data.Product
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonPrimitive

data class TechnicalField(val key: String, val label: String, val unit: String)

val technicalFields = listOf(
    TechnicalField("motor_power_w", "Motor power", "W"),
    TechnicalField("on_off_torque_nm", "On/Off torque", "Nm"),
    TechnicalField("on_off_torque_in_lb", "On/Off torque", "in-lb"),
    TechnicalField("on_off_duty_s4_percent", "On/Off duty S4", "%"),
    TechnicalField("cycles_per_hour", "On/Off cycles", "/h"),
    TechnicalField("modulating_torque_nm", "Modulating torque", "Nm"),
    TechnicalField("modulating_torque_in_lb", "Modulating torque", "in-lb"),
    TechnicalField("modulating_duty_s4_percent", "Modulating duty S4", "%"),
    TechnicalField("starts_per_hour", "Modulating starts", "/h"),
    TechnicalField("shared_torque_nm", "Shared torque¹", "Nm"),
    TechnicalField("shared_torque_in_lb", "Shared torque¹", "in-lb"),
    TechnicalField("shared_duty_s4_percent", "Shared duty S4¹", "%"),
    TechnicalField("operating_time_50hz_s", "Operating time · 50 Hz", "s"),
    TechnicalField("operating_time_60hz_s", "Operating time · 60 Hz", "s"),
    TechnicalField("fla_50hz_a", "FLA · 50 Hz", "A"),
    TechnicalField("fla_60hz_a", "FLA · 60 Hz", "A"),
    TechnicalField("lra_50hz_a", "LRA · 50 Hz", "A"),
    TechnicalField("lra_60hz_a", "LRA · 60 Hz", "A"),
    TechnicalField("operating_time_unqualified_s", "Operating time²", "s"),
    TechnicalField("fla_unqualified_a", "FLA²", "A"),
    TechnicalField("lra_unqualified_a", "LRA²", "A"),
)

fun measurement(product: Product, field: TechnicalField): String {
    val value = product.measurements[field.key]
    return when {
        value is JsonPrimitive && value != JsonNull -> "${value.content} ${field.unit}"
        product.fieldStatus[field.key] == "source_NA" -> "N/A"
        else -> "Not reported"
    }
}

fun relevantFields(products: List<Product>): List<TechnicalField> = technicalFields.filter { field ->
    products.any { it.fieldStatus[field.key] != null && it.fieldStatus[field.key] != "not_in_layout" }
}

fun supply(product: Product): String = buildString {
    append(product.voltage?.content ?: "Not reported")
    append(" V ")
    append(product.current)
    product.phases?.let { append(" · $it phase") }
}

fun fieldNotes(product: Product): List<String> = buildList {
    if (product.serviceLayout == "shared") add("¹ Shared values as published; not separate On/Off and modulating measurements.")
    if (product.measurements.any { (key, value) -> key.contains("unqualified") && value != null && value != JsonNull }) {
        add(if (product.current == "DC") "² Mains frequency does not apply to DC."
            else "² Frequency is not specified for these values in the source.")
    }
    (product.certification["header"] as? JsonPrimitive)?.content?.let { add(it) }
    if ((product.certification["csa_status"] as? JsonPrimitive)?.content == "explicitly_not_CSA_certified") add("Not CSA certified: the source excludes this model. See the source note.")
    product.notes.mapNotNull { (it["text"] as? JsonPrimitive)?.content }.distinct().forEach { add(it) }
}
