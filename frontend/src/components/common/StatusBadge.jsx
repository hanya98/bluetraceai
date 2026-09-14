const styles = {
  'Needs Verification': 'bg-[#ffd4ba] text-[#663520]',
  Resolved: 'bg-[#d9ead7] text-[#1d4b3b]',
  Monitoring: 'bg-[#f8eadf] text-[#663520]',
}

function StatusBadge({ status }) {
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-[11px] font-bold tracking-wide ${
        styles[status] ?? styles['Needs Verification']
      }`}
    >
      {status}
    </span>
  )
}

export default StatusBadge
