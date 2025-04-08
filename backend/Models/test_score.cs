using System.ComponentModel.DataAnnotations.Schema;
using System.ComponentModel.DataAnnotations;

namespace backend.Models
{
    public class test_score
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int id { get; set; }
        public int? user_id { get; set; }
        [ForeignKey("user_id")]
        public users user { get; set; }

        public int? test_id { get; set; }
        [ForeignKey("test_id")]
        public tests test { get; set; }

        public int score { get; set; }
        public DateTimeOffset date { get; set; }
    }
}
